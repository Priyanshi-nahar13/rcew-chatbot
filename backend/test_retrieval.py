from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="embeddings/chroma_db")
collection = client.get_collection("rcew_knowledge")

def search(query, top_k=3):
    query_embedding = model.encode([query])[0].tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    print(f"\nQuery: '{query}'")
    print("─" * 50)
    for i, (doc, meta) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0]
    )):
        print(f"\nResult {i+1} (from {meta['source']}):")
        print(doc[:300] + "..." if len(doc) > 300 else doc)

# Test with real RCEW questions
search("What are the fees for BTech CSE?")
search("Who is the principal of RCEW?")
search("What companies come for placement?")
search("Is hostel facility available?")