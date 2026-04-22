import os
import re
from collections import Counter

LAKE_DIR = "content_lake"

def extract_special_terms():
    # We are looking for: 
    # 1. CamelCaseWords (e.g., NutriDrip)
    # 2. ACRONYMS (e.g., SOP, KPI)
    # 3. Capitalized Proper Nouns (e.g., Zenoti)
    
    pattern = re.compile(r'\b[A-Z][a-z]+[A-Z][a-z]+\b|\b[A-Z]{2,}\b|\b[A-Z][a-z]{3,}\b')
    all_terms = []

    for filename in os.listdir(LAKE_DIR):
        # We process .txt and .md files (skipping CSVs for now as they are too messy)
        if filename.endswith((".txt", ".md")):
            with open(os.path.join(LAKE_DIR, filename), 'r', errors='ignore') as f:
                text = f.read()
                matches = pattern.findall(text)
                all_terms.extend(matches)

    # Filter out common English words that start with capitals at start of sentences
    stop_words = {'The', 'This', 'That', 'With', 'From', 'Your', 'They', 'When'}
    filtered_terms = [t for t in all_terms if t not in stop_words]

    # Get the most frequent 200 terms
    counts = Counter(filtered_terms)
    common_terms = [word for word, count in counts.most_common(200)]
    
    return sorted(list(set(common_terms)))

if __name__ == "__main__":
    keywords = extract_special_terms()
    print(f"Extracted {len(keywords)} unique keywords from your lake.")
    
    with open("custom_vocabulary.txt", "w") as f:
        f.write(", ".join(keywords))
    
    print("✅ Created custom_vocabulary.txt")
