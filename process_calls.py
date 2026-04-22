import os
import json
import subprocess
from openai import OpenAI
from dotenv import load_dotenv
from rapidfuzz import process as fuzz_process, fuzz


load_dotenv()
client = OpenAI()

INPUT_DIR = "input_calls"
OUTPUT_DIR = "processed"
METADATA_DIR = "call_metadata"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Vocab loader
def get_custom_vocab():
    vocab_path = "custom_vocabulary.txt"
    if os.path.exists(vocab_path):
        with open(vocab_path, "r") as f:
            return f.read()
    return ""

# ----------------------------
# FUZZY NAME NORMALIZER
# ----------------------------
def build_canonical_name_list(output_dir):
    names = set()
    if not os.path.exists(output_dir): return []
    for f in os.listdir(output_dir):
        if f.endswith(".json"):
            try:
                with open(os.path.join(output_dir, f)) as fh:
                    rec = json.load(fh)
                    # Correcting the path to the agent name in your schema
                    name = rec.get("analysis", {}).get("agent_name", "")
                    if name and name.lower() not in ("unknown", "n/a"):
                        names.add(name.strip())
            except: continue
    return list(names)


def normalize_agent_name(raw_name, canonical_names, threshold=80):
    """
    If raw_name fuzzy-matches a known canonical name above `threshold`,
    snap to the canonical name. Otherwise keep as-is (it becomes canonical next run).

    threshold=80 is a good default. Lower to 70 if names are still splitting.
    token_sort_ratio handles "Erla Howe" vs "Erla" gracefully.
    """
    if not raw_name or raw_name.strip().lower() in ("unknown", "n/a", ""):
        return "Unknown"

    if not canonical_names:
        return raw_name.strip()

    match, score, _ = fuzz_process.extractOne(
        raw_name,
        canonical_names,
        scorer=fuzz.token_sort_ratio
    )

    if score >= threshold:
        return match
    else:
        return raw_name.strip()


# ----------------------------
# TRANSCRIPTION
# ----------------------------
def transcribe_audio(file_path):
    print(f"🎧 Transcribing with OpenAI: {file_path}")

    vocab = get_custom_vocab()

    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=audio_file,
            prompt=f"""
This is a customer service call for a wellness spa.

Correct terminology:
- lymphatic drainage massage
- signature treatment
- red light therapy add-on
- Midtown / East 54th locations
- appointment booking conversations

Maintain correct spelling of services, names, and locations.

Vocabulary context:
{vocab}
"""
        )

    return transcript.text

# ----------------------------
# DURATION
# ----------------------------
def get_audio_length(file_path):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    try:
        return float(result.stdout.decode().strip())
    except ValueError:
        return None

# ----------------------------
# ANALYSIS
# ----------------------------
# --- NEW HELPER: Fetch Context from Lake ---
def get_knowledge_base_context(category):
    """
    Finds the most relevant SOP or Rubric in the content_lake.
    For now, we will look for files matching the category name or a general 'Rubric' file.
    """
    context = ""
    lake_files = os.listdir("content_lake")
    
    # Try to find a file that matches the category or is a general rubric
    # Example: if category is 'Inbound', look for 'Inbound_SOP.txt'
    for filename in lake_files:
        if "rubric" in filename.lower() or "sop" in filename.lower():
            with open(os.path.join("content_lake", filename), "r") as f:
                context += f"\n--- Source: {filename} ---\n"
                context += f.read()[:2000] # Grab first 2k chars to avoid hitting token limits
    
    return context

# --- UPDATED ANALYSIS FUNCTION ---
def analyze_call(transcript, direction="Unknown"):
    # 1. Pull context from lake
    knowledge_context = get_knowledge_base_context(direction)

    # 2. Use data from the Drive
    prompt = f"""
You are a call QA evaluator for Clean Market.
The direction of this call is: {direction}

### CORPORATE KNOWLEDGE BASE (SOPs & RUBRICS)
Use the following documentation to score the call. If the agent contradicts these SOPs, penalize the 'technical' score.
{knowledge_context}

### TASK
Analyze the transcript and return ONLY valid JSON.

### SCORING RUBRIC (Total 100 points)
- "opening": 0–25 (greeting, intro, rapport)
- "technical": 0–60 (product knowledge, accuracy, objection handling based on SOPs)
- "closing": 0–15 (confirmation, next steps, sign-off)

### FIELDS TO EXTRACT
- "overall": sum of scores (0–100)
- "category": Select the most accurate category based on the transcript.
- "appointment_booked": true/false
- "agent_name": name used by staff
- "location": city or store region
- "title": 5-8 word summary

Return this structure:
{{
  "scores": {{ "opening": 0, "technical": 0, "closing": 0, "overall": 0 }},
  "category": "string",
  "appointment_booked": false,
  "agent_name": "string",
  "location": "string",
  "title": "string"
}}

Transcript:
{transcript}
"""

    response = client.chat.completions.create(
        model="gpt-4o", # You can upgrade to "gpt-4o" for even better SOP adherence
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {"error": "parsing_failed"}

# ----------------------------
# PROCESS FILES
# ----------------------------
skipped = 0
processed = 0
failed = 0

# 1. Build the canonical list ONCE before the loop to save processing time
canonical_names = build_canonical_name_list(OUTPUT_DIR)

for file_name in os.listdir(INPUT_DIR):
    if not file_name.endswith(".mp3"):
        continue

    out_path = os.path.join(OUTPUT_DIR, file_name.replace(".mp3", ".json"))

    # Skip already processed files
    if os.path.exists(out_path):
        print(f"Skipping (already processed): {file_name}")
        skipped += 1
        continue

    file_path = os.path.join(INPUT_DIR, file_name)
    recording_id = file_name.replace(".mp3", "")
    print(f"\nProcessing: {file_name}")

    try:
        # A. Get Metadata first to determine Call Direction
        direction = "Unknown"
        meta_path = os.path.join(METADATA_DIR, f"{recording_id}.json")
        if os.path.exists(meta_path):
            with open(meta_path) as mf:
                meta = json.load(mf)
            direction = meta.get("direction", "Unknown")

        # B. Transcription and Duration
        duration = get_audio_length(file_path)
        created_time = os.path.getmtime(file_path)
        transcript = transcribe_audio(file_path)

        # C. AI Analysis (Now passing direction for better categorization)
        analysis = analyze_call(transcript, direction=direction)

        # D. Normalize Appointment Booked to actual Boolean
        analysis["appointment_booked"] = str(analysis.get("appointment_booked", "")).lower() == "true"

        # E. Robust Score Clamping
        scores = analysis.get("scores", {})
        try:
            opening   = max(0, min(int(float(scores.get("opening", 0))), 25))
            technical = max(0, min(int(float(scores.get("technical", 0))), 60))
            closing   = max(0, min(int(float(scores.get("closing", 0))), 15))
            overall   = opening + technical + closing
            analysis["scores"] = {
                "opening": opening,
                "technical": technical,
                "closing": closing,
                "overall": overall
            }
        except (ValueError, TypeError):
            analysis["scores"] = {"opening": 0, "technical": 0, "closing": 0, "overall": 0}

        # F. Fuzzy Name Normalization
        raw_name = analysis.get("agent_name", "Unknown")
        analysis["agent_name"] = normalize_agent_name(raw_name, canonical_names)

        # G. Final Output Assembly
        output = {
            "file": file_name,
            "created_time": created_time,
            "duration": duration,
            "direction": direction,
            "transcript": transcript,
            "analysis": analysis
        }

        with open(out_path, "w") as f:
            json.dump(output, f, indent=2)

        print(f"✅ Saved: {out_path} | Category: {analysis['category']} | Agent: {analysis['agent_name']}")
        processed += 1

    except Exception as e:
        print(f"❌ Failed {file_name}: {e}")
        failed += 1

print(f"\n--- Done ---")
print(f"Processed: {processed} | Skipped: {skipped} | Failed: {failed}")
