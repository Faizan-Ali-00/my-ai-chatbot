import streamlit as st
from groq import Groq
from pathlib import Path
from pypdf import PdfReader
from datetime import datetime
import json
import os
import re

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Nexus AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CURRENT DATE
# ============================================================

CURRENT_DATE = datetime.now().strftime("%B %d, %Y")

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent;}

    .main-title {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem; font-weight: 800; text-align: center;
        padding: 1rem 0 0.5rem 0; margin-bottom: 0;
    }
    .subtitle { text-align: center; color: #a0a0b0; font-size: 1rem; margin-bottom: 2rem; }

    div[data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px; padding: 1rem; margin: 0.5rem 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]) {
        background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%);
        border-left: 4px solid #667eea;
    }
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]) {
        background: linear-gradient(135deg, #f093fb22 0%, #f5576c22 100%);
        border-left: 4px solid #f5576c;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
        display: block !important;
    }
    section[data-testid="stSidebar"] h2 { color: #667eea; }

    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; border-radius: 10px;
        padding: 0.5rem 1rem; font-weight: 600;
        transition: all 0.3s ease; width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
    }

    .stChatInput textarea {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(102, 126, 234, 0.3) !important;
        border-radius: 15px !important;
        color: white !important; font-size: 1rem !important;
    }
    .stChatInput textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2) !important;
    }

    hr { border-color: rgba(255, 255, 255, 0.1); margin: 1rem 0; }
    .stSpinner > div { border-top-color: #667eea !important; }
    .stAlert { border-radius: 10px; background: rgba(255, 255, 255, 0.05); }
    p, h1, h2, h3, h4, h5, h6, span, div { color: #e0e0e8; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CLEAN RESPONSE
# ============================================================

META_STARTERS = [
    "Identify the", "Determine the", "Analyze the",
    "Let me ", "Okay, ", "Hmm, ", "Wait, ",
    "I need to ", "The user is asking", "The user's",
    "Draft Response:", "Final decision:",
    "Let's ", "Actually, ", "Correction:",
    "Alternative:", "Refine:", "Check constraints",
    "Final Output",
]

def clean_response(text):
    if not text:
        return ""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"</?think>", "", cleaned)

    lines = cleaned.split("\n")
    filtered = []
    for line in lines:
        stripped = line.strip()
        if any(stripped.startswith(m) for m in META_STARTERS):
            continue
        filtered.append(line)
    cleaned = "\n".join(filtered)

    if not cleaned.strip() and text:
        parts = text.strip().split("\n\n")
        cleaned = parts[-1] if parts else ""

    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()

# ============================================================
# API KEY
# ============================================================

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("🔑 **API key not found.**")
    st.info("Add `GROQ_API_KEY` to `.env` or Streamlit Secrets.")
    st.stop()

# ============================================================
# MODEL
# ============================================================

try:
    MODEL_NAME = st.secrets["MODEL_NAME"]
except Exception:
    MODEL_NAME = "qwen/qwen3.6-27b"

# ============================================================
# FILES
# ============================================================

DOCUMENTS_DIR = Path("documents")
DOCUMENTS_DIR.mkdir(exist_ok=True)
HISTORY_FILE = Path("chat_history.json")

# ============================================================
# CLIENT
# ============================================================

@st.cache_resource
def get_client():
    return Groq(api_key=GROQ_API_KEY)

client = get_client()

# ============================================================
# LOAD / SAVE CHATS
# ============================================================

def load_chats():
    if not HISTORY_FILE.exists():
        return {"New Chat": []}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            chats = json.load(file)
        if not chats:
            return {"New Chat": []}
        for chat_name, msgs in chats.items():
            for msg in msgs:
                if msg.get("role") == "assistant":
                    msg["content"] = clean_response(msg.get("content", ""))
        return chats
    except Exception:
        return {"New Chat": []}


def save_chats():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as file:
            json.dump(st.session_state.chats, file, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Could not save chats: {e}")

# ============================================================
# SESSION STATE
# ============================================================

if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

if "current_chat" not in st.session_state:
    st.session_state.current_chat = list(st.session_state.chats.keys())[0]

# ============================================================
# CREATE NEW CHAT
# ============================================================

def create_new_chat():
    number = 1
    while f"New Chat {number}" in st.session_state.chats:
        number += 1
    chat_name = f"New Chat {number}"
    st.session_state.chats[chat_name] = []
    st.session_state.current_chat = chat_name
    save_chats()

# ============================================================
# PDF FUNCTIONS
# ============================================================

def extract_pdf_text(file_path):
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception:
        return ""
    return text


def load_documents():
    documents = []
    for file in DOCUMENTS_DIR.glob("*.pdf"):
        text = extract_pdf_text(file)
        if text.strip():
            documents.append({"name": file.name, "text": text})
    return documents


def find_relevant_context(question):
    documents = load_documents()
    if not documents:
        return ""
    question_words = set(question.lower().split())
    best_document = None
    best_score = 0
    for document in documents:
        document_words = set(document["text"].lower().split())
        score = len(question_words.intersection(document_words))
        if score > best_score:
            best_score = score
            best_document = document
    if best_document is None:
        return ""
    return f"Document: {best_document['name']}\n\n{best_document['text'][:4000]}"

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 💬 Conversations")
    st.markdown("---")

    if st.button("➕  New Chat", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.markdown("### 📚 Your Chats")
    chat_names = list(st.session_state.chats.keys())
    for chat_name in chat_names:
        is_current = chat_name == st.session_state.current_chat
        button_text = ("▶  " if is_current else "💬  ") + chat_name
        if st.button(button_text, key=f"chat_{chat_name}", use_container_width=True):
            st.session_state.current_chat = chat_name
            st.rerun()

    st.markdown("---")

    if st.button("🗑️  Delete Current Chat", use_container_width=True):
        current = st.session_state.current_chat
        if len(st.session_state.chats) > 1:
            del st.session_state.chats[current]
            st.session_state.current_chat = list(st.session_state.chats.keys())[0]
        else:
            st.session_state.chats[current] = []
        save_chats()
        st.rerun()

# ============================================================
# MAIN PAGE
# ============================================================

current_chat = st.session_state.current_chat
messages = st.session_state.chats[current_chat]

st.markdown('<h1 class="main-title">✨ Nexus AI</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Your intelligent assistant · Ask anything</p>',
    unsafe_allow_html=True
)

# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in messages:
    with st.chat_message(message["role"]):
        content = message["content"]
        if message["role"] == "assistant":
            content = clean_response(content)
        st.markdown(content)

# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input("✨ Ask me anything...")

# ============================================================
# PROCESS MESSAGE
# ============================================================

if prompt:
    messages.append({"role": "user", "content": prompt})

    if current_chat.startswith("New Chat"):
        words = prompt.split()
        title = " ".join(words[:6]) + ("..." if len(words) > 6 else "")
        title = title[:40]

        original_title = title
        number = 2
        while title in st.session_state.chats and title != current_chat:
            title = f"{original_title} {number}"
            number += 1

        if title != current_chat:
            st.session_state.chats[title] = messages
            del st.session_state.chats[current_chat]
            st.session_state.current_chat = title
            current_chat = title
            messages = st.session_state.chats[title]
            save_chats()

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("✨ Thinking..."):
            try:
                recent_messages = messages[-4:]
                context = find_relevant_context(prompt)

                system_prompt = f"""You are Nexus AI, a smart, friendly, and helpful assistant.

Today's date is {CURRENT_DATE}.

YOUR ROLE:
- Answer ANY question the user asks — general knowledge, math, coding, science, history, sports, advice, writing, translation, etc.
- Be confident and helpful. If you know something, share it.
- If you truly don't know something (like live weather or breaking news), say so briefly.
- Never refuse a reasonable question.

RESPONSE STYLE:
- Respond ONLY with the final answer.
- Do NOT show reasoning, thinking, or step-by-step analysis.
- Do NOT use phrases like "Let me think", "Okay", "Wait", "Hmm", "The user is asking".
- Do NOT use "Correction:" or self-correct mid-answer.
- Do NOT reference "the system prompt" or "the instructions".
- Be direct, clear, and natural.

For simple questions: answer in 1-2 sentences.
For list questions: give a clean numbered list, no corrections.
For complex topics: give a clear, structured explanation.
For coding questions: provide clean, working code with brief explanation.
For math: show the calculation and final answer.

If document info is provided below, use it. Do not invent facts from documents."""

                if context:
                    system_prompt += f"\n\nRelevant document information:\n\n{context}"

                api_messages = [{"role": "system", "content": system_prompt}]
                api_messages.extend(recent_messages)

                try:
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=api_messages,
                        max_tokens=1000,
                        temperature=0.3,
                        extra_body={"reasoning_effort": "none"}
                    )
                except Exception:
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=api_messages,
                        max_tokens=1050,
                        temperature=0.3
                    )

                answer = response.choices[0].message.content
                answer = clean_response(answer)

                if not answer:
                    answer = "I couldn't generate a final answer. Please try again."

                st.markdown(answer)
                messages.append({"role": "assistant", "content": answer})
                save_chats()

            except Exception as e:
                st.error("⚠️ Something went wrong. Please try again.")
                st.code(str(e))

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.markdown(
    '<p style="text-align:center; color:#667eea; font-size:0.85rem;">'
    '✨ Nexus AI'
    '</p>',
    unsafe_allow_html=True
)
