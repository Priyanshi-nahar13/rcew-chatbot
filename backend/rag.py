import os
import warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb
from groq import Groq

load_dotenv()

# ── Load models once (reused across calls) ──────────────────
print("Loading RAG pipeline...")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="embeddings/chroma_db")
collection = chroma_client.get_collection("rcew_knowledge")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
print("RAG pipeline ready!")

# ── System prompt ────────────────────────────────────────────
SYSTEM_PROMPT = """You are RCEW Assistant, the official AI chatbot for
Rajasthan College of Engineering for Women (RCEW), Jaipur.

Your job is to answer students' and parents' questions about RCEW
using ONLY the context provided below.

Rules:
- NEVER say "According to the context", "Based on the context",
  "As per the context", "The context says", "From the context" or
  any similar phrase. Just answer directly and confidently.
- Answer clearly and helpfully in the same language the user writes in
- If the answer is in the context, answer confidently and completely
- For placement questions, always list ALL company names you find in context
- If the answer is NOT in the context, say:
  "I don't have that information right now. Please contact RCEW directly
   at 9001099930 or visit www.rcew.ac.in"
- Never make up fees, dates, names, or facts
- Keep answers concise but complete
- Use bullet points for lists (fees, facilities, companies etc.)
- Understand that users may ask in informal or broken English —
  interpret the intent, not just the exact words
- Sound like a helpful college assistant, not a robot reading a document
"""

# ── Query expander ───────────────────────────────────────────
def expand_query(query: str) -> str:
    """Add synonyms to improve retrieval for common question types."""
    q = query.lower()

    if any(w in q for w in ["compan", "recruiter", "placement", "job",
                              "hired", "campus", "came", "visit", "package"]):
        return query + " companies recruiters placement hired campus drive"

    if any(w in q for w in ["fee", "fees", "cost", "charge", "tuition",
                              "kitna", "price", "pay", "money"]):
        return query + " fee tuition cost per year"

    if any(w in q for w in ["hostel", "room", "stay", "accommodation",
                              "boarding", "raha", "rahi"]):
        return query + " hostel room facilities bed"

    if any(w in q for w in ["admit", "admission", "join", "apply",
                              "eligib", "document", "process", "reap"]):
        return query + " admission eligibility process documents required"

    if any(w in q for w in ["cse", "computer", "branch", "department",
                              "dept", "ece", "civil", "ee", "aids", "ai"]):
        return query + " CSE department computer science engineering faculty"

    if any(w in q for w in ["contact", "phone", "address", "email",
                              "location", "where", "number"]):
        return query + " contact phone address location number"

    if any(w in q for w in ["scholarship", "scholarship", "concession",
                              "discount", "waiver"]):
        return query + " scholarship fee concession merit"

    if any(w in q for w in ["bus", "transport", "conveyance", "route"]):
        return query + " bus transport conveyance route"

    if any(w in q for w in ["lab", "laborator", "infrastructure",
                              "facility", "facilities"]):
        return query + " laboratory infrastructure facilities"

    return query


# ── Retrieval ─────────────────────────────────────────────────
def retrieve_context(query: str, top_k: int = 6) -> str:
    """Convert query to embedding and find most relevant chunks."""
    query_embedding = embed_model.encode([query])[0].tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    chunks  = results["documents"][0]
    sources = [m["source"] for m in results["metadatas"][0]]

    context_parts = []
    for chunk, source in zip(chunks, sources):
        context_parts.append(f"[Source: {source}]\n{chunk}")

    return "\n\n---\n\n".join(context_parts)


# ── Main chat function ────────────────────────────────────────
def chat(query: str, history: list = []) -> dict:
    """
    Takes a query + chat history, returns answer + sources.
    history format: [{"role": "user",      "content": "..."},
                     {"role": "assistant", "content": "..."}]
    """
    # Step 1: Expand query for better retrieval
    expanded_query = expand_query(query)

    # Step 2: Retrieve relevant context using expanded query
    context = retrieve_context(expanded_query, top_k=6)

    # Step 3: Build messages — original query goes to LLM (natural tone)
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + f"\n\nCONTEXT:\n{context}"
        }
    ]

    # Add last 6 messages for conversation memory
    messages.extend(history[-6:])

    # Add current user question (original, not expanded)
    messages.append({"role": "user", "content": query})

    # Step 4: Call Groq LLM
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3,    # low = factual answers
        max_tokens=512,
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "context_used": context[:500] + "..."
    }

def chat_stream(query: str, history: list = []):
    """
    Same as chat() but streams the response word by word.
    Yields text chunks as they arrive from Groq.
    """
    expanded_query = expand_query(query)
    context = retrieve_context(expanded_query, top_k=6)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + f"\n\nCONTEXT:\n{context}"
        }
    ]
    messages.extend(history[-6:])
    messages.append({"role": "user", "content": query})

    # stream=True makes Groq send words as they generate
    stream = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3,
        max_tokens=512,
        stream=True        # ← only change from chat()
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta    # send each word/token as it arrives


# ── Test when run directly ────────────────────────────────────
if __name__ == "__main__":
    history = []
    test_questions = [
        "What is the BTech CSE fee at RCEW?",
        "Tell me about hostel facilities",
        "which companies came in the college",           # informal phrasing
        "kaun si companies aati hain placement ke liye", # Hindi phrasing
        "What is the admission process and eligibility?",
        "Tell me about the CSE department",
        "kitni fee hai btech ki",                        # Hindi fee question
        "What is the contact number and address of RCEW?",
    ]

    for q in test_questions:
        print(f"\nQ: {q}")
        result = chat(q, history)
        print(f"A: {result['answer']}")
        print("─" * 60)
        history.append({"role": "user",      "content": q})
        history.append({"role": "assistant", "content": result["answer"]})