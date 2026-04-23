import json
import os
import warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore")

from sentence_transformers import SentenceTransformer
import chromadb

# ── Load scraped chunks ──────────────────────────────────────
print("Loading chunks...")
with open("data/processed/rcew_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)
print(f"  Scraped chunks loaded : {len(chunks)}")

# ── Load manual knowledge entries ────────────────────────────
try:
    with open("data/processed/rcew_manual.json", "r", encoding="utf-8") as f:
        manual_pages = json.load(f)
    for i, page in enumerate(manual_pages):
        chunks.append({
            "chunk_id": f"manual_{i}",
            "source":   page["source"],
            "text":     page["text"]
        })
    print(f"  Manual entries added  : {len(manual_pages)}")
except FileNotFoundError:
    print("  No manual data file found, skipping")

print(f"  Total chunks to embed : {len(chunks)}")

# ── Load embedding model ─────────────────────────────────────
print("\nLoading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# ── Extract texts, IDs, metadata ─────────────────────────────
texts = [c["text"]               for c in chunks]
ids   = [c["chunk_id"]           for c in chunks]
meta  = [{"source": c["source"]} for c in chunks]

# ── Generate embeddings ──────────────────────────────────────
print(f"Generating embeddings for {len(texts)} chunks...")
embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
print("Embeddings done!")

# ── Store in ChromaDB ─────────────────────────────────────────
os.makedirs("embeddings", exist_ok=True)
client = chromadb.PersistentClient(path="embeddings/chroma_db")

# Clear old collection before rebuilding
try:
    client.delete_collection("rcew_knowledge")
    print("Cleared old collection.")
except:
    pass

collection = client.create_collection(
    name="rcew_knowledge",
    metadata={"hnsw:space": "cosine"}
)

# ── Add in batches ────────────────────────────────────────────
BATCH = 100
for i in range(0, len(chunks), BATCH):
    end = min(i + BATCH, len(chunks))
    collection.add(
        ids=ids[i:end],
        embeddings=embeddings[i:end].tolist(),
        documents=texts[i:end],
        metadatas=meta[i:end]
    )
    print(f"  Stored chunks {i+1}–{end}")

print(f"\n{'─'*50}")
print(f"  Total vectors stored : {collection.count()}")
print(f"  Manual entries       : {len(manual_pages)}")
print(f"  Database location    : embeddings/chroma_db/")
print(f"{'─'*50}")