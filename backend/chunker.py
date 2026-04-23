import json
import os

# Load cleaned data
with open("data/processed/rcew_clean.json", "r", encoding="utf-8") as f:
    pages = json.load(f)

def chunk_text(text, source, chunk_size=500, overlap=50):
    """Split text into overlapping chunks of ~chunk_size characters."""
    chunks = []
    start = 0
    chunk_id = 0

    while start < len(text):
        end = start + chunk_size

        # Don't cut in the middle of a word — find last space before end
        if end < len(text):
            last_space = text.rfind(" ", start, end)
            if last_space != -1:
                end = last_space

        chunk_text = text[start:end].strip()

        if len(chunk_text) > 50:  # skip tiny chunks
            chunks.append({
                "chunk_id": f"{source}_{chunk_id}",
                "source": source,
                "text": chunk_text
            })
            chunk_id += 1

        start = end - overlap  # overlap so context isn't lost at boundaries

    return chunks

# Chunk all pages
all_chunks = []
for page in pages:
    chunks = chunk_text(page["text"], source=page["page"])
    all_chunks.extend(chunks)
    print(f"  {page['page']:40s} → {len(chunks)} chunks")

os.makedirs("data/processed", exist_ok=True)
with open("data/processed/rcew_chunks.json", "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, ensure_ascii=False, indent=2)

print(f"\n{'─'*50}")
print(f"  Total chunks created : {len(all_chunks)}")
print(f"  Saved to             : data/processed/rcew_chunks.json")
print(f"{'─'*50}")