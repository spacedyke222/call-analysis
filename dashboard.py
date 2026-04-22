import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime

DATA_DIR = "processed"

st.set_page_config(page_title="Clean Market QA", layout="wide")
st.title("📞 Call Analysis Dashboard")

# ----------------------------
# LOAD DATA (Same as before)
# ----------------------------
def safe_str(x):
    if isinstance(x, dict): return x.get("name") or str(x)
    if isinstance(x, list): return ", ".join(map(str, x))
    return str(x) if x is not None else "Unknown"

@st.cache_data(ttl=60)
def load_all_data():
    all_data = []
    if not os.path.exists(DATA_DIR): return pd.DataFrame()
    for file in os.listdir(DATA_DIR):
        if not file.endswith(".json"): continue
        with open(os.path.join(DATA_DIR, file)) as f:
            record = json.load(f)
        
        analysis = record.get("analysis", {})
        scores = analysis.get("scores", {})
        start_ts = record.get("created_time", 0)
        duration = record.get("duration", 0) or 0
        start_dt = datetime.fromtimestamp(start_ts)
        end_dt = datetime.fromtimestamp(start_ts + duration)

        all_data.append({
            "id": record.get("file"),
            "Date": start_dt.strftime("%Y-%m-%d"),
            "Start": start_dt.strftime("%H:%M:%S"),
            "End": end_dt.strftime("%H:%M:%S"),
            "agent": safe_str(analysis.get("agent_name")),
            "category": safe_str(analysis.get("category")),
            "overall": scores.get("overall", 0),
            "opening": scores.get("opening", 0),
            "technical": scores.get("technical", 0),
            "closing": scores.get("closing", 0),
            "booked": analysis.get("appointment_booked", False),
            "location": safe_str(analysis.get("location")),
            "title": safe_str(analysis.get("title")),
            "transcript": record.get("transcript", ""),
            "raw_timestamp": start_ts
        })
    return pd.DataFrame(all_data)

df = load_all_data()

if df.empty:
    st.warning("No data found in 'processed' folder.")
    st.stop()

# ----------------------------
# SIDEBAR & FILTERS
# ----------------------------
st.sidebar.header("Global Filters")
agents = ["All"] + sorted(df["agent"].unique().tolist())
selected_agent = st.sidebar.selectbox("Agent", agents)

filtered_df = df.copy()
if selected_agent != "All": 
    filtered_df = filtered_df[filtered_df["agent"] == selected_agent]
filtered_df = filtered_df.sort_values("raw_timestamp", ascending=False)

# ----------------------------
# KPI METRICS
# ----------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Calls", len(filtered_df))
c2.metric("Avg Score", f"{filtered_df['overall'].mean():.1f}")
c3.metric("Bookings", int(filtered_df["booked"].sum()))
c4.metric("Conversion", f"{(filtered_df['booked'].sum()/len(filtered_df)*100):.1f}%")

st.divider()

# ----------------------------
# COMPATIBILITY UI: SELECTBOX + TABLE
# ----------------------------
col_list, col_detail = st.columns([1, 1])

with col_list:
    st.subheader("Recent Calls")
    # Instead of clicking the table, we use this selector to pick the call
    call_options = filtered_df.apply(lambda x: f"{x['Date']} {x['Start']} - {x['agent']} ({x['overall']}%)", axis=1).tolist()
    selected_call_label = st.selectbox("Select a call to inspect:", call_options)
    
    # Still show the table for easy browsing
    st.dataframe(
        filtered_df[["Date", "Start", "agent", "overall", "booked"]],
        use_container_width=True,
        hide_index=True
    )

with col_detail:
    # Find the data for the selected call
    call_idx = call_options.index(selected_call_label)
    call = filtered_df.iloc[call_idx]

    st.subheader(f"🔍 Analysis: {call['title']}")

    # --- AUDIO PLAYER ---
    # Using the recording_id to find the local file
    raw_id = str(call['id'])
    
    # If the ID doesn't already end in .mp3, add it
    if not raw_id.lower().endswith(".mp3"):
        audio_filename = f"{raw_id}.mp3"
    else:
        audio_filename = raw_id

    audio_file_path = os.path.join("input_calls", audio_filename)

    if os.path.exists(audio_file_path):
        with open(audio_file_path, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3")
    else:
        st.error(f"⚠️ Audio missing: {audio_filename}")
    # -------------------------
    
    t1, t2, t3 = st.columns(3)
    t1.write(f"**Start:** {call['Start']}")
    t2.write(f"**End:** {call['End']}")
    t3.write(f"**Booked:** {'✅ Yes' if call['booked'] else '❌ No'}")

    st.write("### 📊 Scoring Breakdown")
    s1, s2, s3 = st.columns(3)
    s1.metric("Opening", f"{call['opening']}/25")
    s2.metric("Technical", f"{call['technical']}/60")
    s3.metric("Closing", f"{call['closing']}/15")
    
    st.progress(int(call['overall']) / 100)

    with st.expander("View Full Transcript", expanded=True):
        st.write(call["transcript"])
