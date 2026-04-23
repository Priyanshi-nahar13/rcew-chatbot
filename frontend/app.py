import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="RCEW Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer    {visibility: hidden;}
    header    {visibility: hidden;}

    .rcew-header {
        background: linear-gradient(135deg, #8B1A1A, #C0392B);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1.5rem;
        color: white;
    }
    .rcew-header h1 { color: white; margin: 0; font-size: 1.8rem; }
    .rcew-header p  { color: #ffcccc; margin: 0.3rem 0 0; font-size: 0.9rem; }
    .stChatInput input { border-radius: 25px !important; }
    .sidebar-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #8B1A1A;
        margin-bottom: 0.5rem;
    }

    /* Make chat area centered even in wide mode */
    .main .block-container {
        max-width: 860px;
        margin: 0 auto;
        padding-top: 1rem;
    }

    [data-testid="stSidebar"] {
    background-color: #fdf5f5;
    border-right: 1px solid #e8d0d0;
    min-width: 220px !important;
    max-width: 280px !important;
}

    /* Force sidebar to always show */
    [data-testid="stSidebar"][aria-expanded="false"] {
    min-width: 220px !important;
    margin-left: 0 !important;
    transform: none !important;
    display: block !important;
}
    section[data-testid="stSidebarContent"] {
    display: block !important;
    visibility: visible !important;
}
    [data-testid="stSidebar"] .stButton button {
        background-color: white;
        border: 1px solid #e0a0a0;
        color: #8B1A1A;
        border-radius: 8px;
        font-size: 0.82rem;
        text-align: left;
        padding: 0.4rem 0.8rem;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #8B1A1A;
        color: white;
        border-color: #8B1A1A;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="rcew-header">
    <h1>🎓 RCEW Assistant</h1>
    <p>AI Chatbot for Rajasthan College of Engineering for Women, Jaipur</p>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "👋 **Namaste! I'm RCEW Assistant.**\n\n"
            "I can help you with:\n"
            "- 💰 Fee structure & scholarships\n"
            "- 🏢 Placement companies & packages\n"
            "- 🏠 Hostel facilities & fees\n"
            "- 📚 Departments & programs\n"
            "- 📋 Admission process & eligibility\n"
            "- 📍 Contact & address\n\n"
            "Feel free to ask in **English or Hindi!**"
        )
    })

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# ── Backend call ──────────────────────────────────────────────
def get_answer_stream(question: str):
    """
    Calls streaming endpoint and yields text chunks.
    Used with st.write_stream() for typing animation.
    """
    try:
        with requests.post(
            f"{API_URL}/chat/stream",
            json={
                "question": question,
                "history": [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
            },
            timeout=120,
            stream=True     # important — tells requests to stream
        ) as response:
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    yield chunk.decode("utf-8")

    except requests.exceptions.ConnectionError:
        yield (
            "⚠️ **Backend server not running!**\n\n"
            "Please start it:\n"
            "```\npython -m uvicorn main:app --reload --port 8000\n```"
        )
    except Exception as e:
        yield f"⚠️ Error: {e}"


# ── Display chat history ──────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Handle pending question ───────────────────────────────────
if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None

    with st.chat_message("user"):
        st.markdown(question)
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("assistant"):
        answer = st.write_stream(get_answer_stream(question))
    st.session_state.messages.append({"role": "assistant", "content": answer})

# ── Chat input ────────────────────────────────────────────────
if prompt := st.chat_input("Ask anything about RCEW.."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        answer = st.write_stream(get_answer_stream(prompt))
    st.session_state.messages.append({"role": "assistant", "content": answer})


# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    # Logo/Title
    st.markdown("""
    <div style='text-align:center; padding: 0.5rem 0 1rem'>
        <div style='font-size:2rem'>🎓</div>
        <div style='font-weight:600; color:#8B1A1A; font-size:1rem'>RCEW Assistant</div>
        <div style='font-size:0.75rem; color:gray'>Powered by Llama 3.3 + RAG</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Suggested questions
    st.markdown('<p class="sidebar-title">💡 SUGGESTED QUESTIONS</p>',
                unsafe_allow_html=True)

    questions = [
        "What is the BTech fee?",
        "What are the hostel facilities?",
        "Which companies come for placement?",
        "What is the admission process?",
        "What is the location of RCEW?",
        "Tell me about CSE department",
        "How to get scholarship?",
        "Contact number of RCEW?",
        "What is MBA fee?",
        "Tell me about ECE department",
    ]

    for q in questions:
        if st.button(q, use_container_width=True, key=q):
            st.session_state.pending_question = q
            st.rerun()

    st.divider()

    # Clear + message count
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pending_question = None
            st.rerun()
    with col2:
        st.metric("Chats", len(st.session_state.messages))

    st.divider()

    # College info at bottom
    st.markdown("""
    <div style='font-size:0.75rem; color:gray; text-align:center; 
                line-height:1.6'>
        📍 Ajmer Road, Bhakrota<br>
        Jaipur, Rajasthan 302026<br>
        📞 9001099930<br>
        🌐 www.rcew.ac.in
    </div>
    """, unsafe_allow_html=True)