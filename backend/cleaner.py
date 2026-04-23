import json, re, os

with open("data/raw/rcew_raw.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

def clean(text):
    text = re.sub(r'\n{3,}', '\n\n', text)        # max 2 blank lines
    text = re.sub(r'[ \t]+', ' ', text)            # collapse spaces/tabs
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)    # remove non-ASCII
    text = re.sub(r'(Previous|Next|\|\|)\s*', '', text)  # remove nav leftovers
    return text.strip()

cleaned, skipped = [], 0
for page in raw:
    t = clean(page["text"])
    if len(t) < 150:          # skip near-empty pages
        skipped += 1
        continue
    cleaned.append({
        "source": page["url"],
        "page":   page["page"],
        "text":   t,
        "chars":  len(t)
    })

os.makedirs("data/processed", exist_ok=True)
with open("data/processed/rcew_clean.json", "w", encoding="utf-8") as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

print(f"Cleaned {len(cleaned)} pages  |  Skipped {skipped} (too short)")
print(f"Total chars: {sum(p['chars'] for p in cleaned):,}")
print("Saved → data/processed/rcew_clean.json")