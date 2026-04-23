import os
import warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from rag import chat, chat_stream

app = FastAPI(title="RCEW Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    history: List[Message] = []

class ChatResponse(BaseModel):
    answer: str
    status: str = "ok"

@app.on_event("startup")
async def warmup():
    print("Warming up RAG pipeline...")
    try:
        chat("hello", [])
        print("Warmup complete — chatbot ready!")
    except Exception as e:
        print(f"Warmup error (non-critical): {e}")

@app.get("/")
def root():
    return {"message": "RCEW Chatbot API is running!"}

@app.get("/health")
def health():
    return {"status": "healthy", "model": "llama-3.3-70b-versatile"}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in req.history]
    result = chat(req.question, history)
    return ChatResponse(answer=result["answer"])

# ── New streaming endpoint ────────────────────────────────────
@app.post("/chat/stream")
def chat_stream_endpoint(req: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in req.history]

    def generate():
        for chunk in chat_stream(req.question, history):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )