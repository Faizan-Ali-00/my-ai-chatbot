import streamlit as st
from pathlib import Path
from pypdf import PdfReader
from datetime import datetime
import json
import os
import re
import base64
import requests

# --- Provider SDKs ---
from cerebras.cloud.sdk import Cerebras

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Nexus AI",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# LOGO — Nexus Atom
# ============================================================

LOGO_SVG = """
<svg viewBox="0 0 720 240" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="nucleusGrad" cx="35%" cy="30%" r="75%">
      <stop offset="0%" stop-color="#c9b8ff"/>
      <stop offset="45%" stop-color="#8b5cf6"/>
      <stop offset="80%" stop-color="#6d28d9"/>
      <stop offset="100%" stop-color="#2b1256"/>
    </radialGradient>
    <linearGradient id="textGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#8A6BFF"/>
      <stop offset="50%" stop-color="#C77DFF"/>
      <stop offset="100%" stop-color="#6BD6FF"/>
    </linearGradient>
    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="9" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <filter id="softGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <rect width="720" height="240" fill="#0b0715" rx="24"/>

  <!-- Atom group -->
  <g transform="translate(120, 120)">

    <!-- Orbit 1 — diagonal -->
    <ellipse cx="0" cy="0" rx="70" ry="28"
             fill="none" stroke="#8b5cf6" stroke-width="2.5"
             stroke-opacity="0.55"
             transform="rotate(45)"/>

    <!-- Orbit 2 — opposite diagonal -->
    <ellipse cx="0" cy="0" rx="70" ry="28"
             fill="none" stroke="#a78bff" stroke-width="2.5"
             stroke-opacity="0.55"
             transform="rotate(-45)"/>

    <!-- Orbit 3 — horizontal -->
    <ellipse cx="0" cy="0" rx="70" ry="28"
             fill="none" stroke="#C77DFF" stroke-width="2.5"
             stroke-opacity="0.5"/>

    <!-- Electrons (small dots on orbits) -->
    <circle cx="49" cy="49" r="4.5" fill="#E0C3FF" filter="url(#softGlow)"/>
    <circle cx="49" cy="-49" r="4.5" fill="#E0C3FF" filter="url(#softGlow)"/>
    <circle cx="70" cy="0" r="4.5" fill="#E0C3FF" filter="url(#softGlow)"/>

    <!-- Glowing nucleus -->
    <g filter="url(#glow)">
      <circle cx="0" cy="0" r="26" fill="url(#nucleusGrad)"/>
    </g>
    <circle cx="0" cy="0" r="18" fill="none" stroke="#ffffff" stroke-opacity="0.2" stroke-width="1.5"/>
  </g>

  <!-- Wordmark "Nexus AI" -->
  <text x="245" y="130"
        font-family="'Inter','Segoe UI',Arial,Helvetica,sans-serif"
        font-size="72" font-weight="900"
        fill="url(#textGrad)"
        letter-spacing="-2">Nexus AI</text>

  <!-- Tagline -->
  <text x="250" y="172"
        font-family="'Inter','Segoe UI',Arial,Helvetica,sans-serif"
        font-size="15" font-weight="500"
        fill="#b8b2d6"
        letter-spacing="3">YOUR INTELLIGENT ASSISTANT</text>

  <!-- Accent dot -->
  <circle cx="510" cy="122" r="6" fill="#C77DFF" opacity="0.95"/>
</svg>
"""

ICON_SVG = """
<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="nucleusGrad2" cx="35%" cy="30%" r="75%">
      <stop offset="0%" stop-color="#c9b8ff"/>
      <stop offset="45%" stop-color="#8b5cf6"/>
      <stop offset="80%" stop-color="#6d28d9"/>
      <stop offset="100%" stop-color="#2b1256"/>
    </radialGradient>
    <filter id="glow2" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="7" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <filter id="softGlow2" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2.5" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <rect width="200" height="200" rx="44" fill="#0b0715"/>

  <g transform="translate(100, 100)">
    <!-- Orbits -->
    <ellipse cx="0" cy="0" rx="62" ry="24"
             fill="none" stroke="#8b5cf6" stroke-width="3"
             stroke-opacity="0.55"
             transform="rotate(45)"/>
    <ellipse cx="0" cy="0" rx="62" ry="24"
             fill="none" stroke="#a78bff" stroke-width="3"
             stroke-opacity="0.55"
             transform="rotate(-45)"/>
    <ellipse cx="0" cy="0" rx="62" ry="24"
             fill="none" stroke="#C77DFF" stroke-width="3"
             stroke-opacity="0.5"/>

    <!-- Electrons -->
    <circle cx="43" cy="43" r="5" fill="#E0C3FF" filter="url(#softGlow2)"/>
    <circle cx="43" cy="-43" r="5" fill="#E0C3FF" filter="url(#softGlow2)"/>
    <circle cx="62" cy="0" r="5" fill="#E0C3FF" filter="url(#softGlow2)"/>

    <!-- Nucleus -->
    <g filter="url(#glow2)">
      <circle cx="0" cy="0" r="28" fill="url(#nucleusGrad2)"/>
    </g>
    <circle cx="0" cy="0" r="20" fill="none" stroke="#ffffff" stroke-opacity="0.22" stroke-width="2"/>
  </g>
</svg>
"""


def svg_to_data_uri(svg_string: str) -> str:
    encoded = base64.b64encode(svg_string.strip().encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


LOGO_DATA_URI = svg_to_data_uri(LOGO_SVG)
ICON_DATA_URI = svg_to_data_uri(ICON_SVG)

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

    /* Header logo */
    .nexus-header {
        display: flex;
        justify-content: center;
        padding: 1.2rem 0 0.6rem 0;
    }
    .nexus-header img {
        width: 100%;
        max-width: 460px;
        height: auto;
        filter: drop-shadow(0 20px 50px rgba(139, 92, 246, 0.35));
    }

    /* Sidebar brand logo */
    .side-logo {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 1rem;
    }
    .side-logo img {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        box-shadow: 0 4px 14px rgba(139, 92, 246, 0.4);
    }
    .side-logo-text {
        font-size: 1.1rem;
        font-weight: 800;
        letter-spacing: -0.4px;
        background: linear-gradient(90deg, #8A6BFF, #C77DFF, #6BD6FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
    }
    .side-logo-sub {
        font-size: 0.62rem;
        color: #8b84b5;
        letter-spacing: 0.6px;
        margin-top: 1px;
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
# API KEYS
# ============================================================

def _get_secret(name):
    try:
        return st.secrets[name]
    except Exception:
        return os.getenv(name)

CEREBRAS_API_KEY = _get_secret("CEREBRAS_API_KEY")
CLOUDFLARE_API_KEY = _get_secret("CLOUDFLARE_API_KEY")
CLOUDFLARE_ACCOUNT_ID = _get_secret("CLOUDFLARE_ACCOUNT_ID")
OPENROUTER_API_KEY = _get_secret("OPENROUTER_API_KEY")

if not any([CEREBRAS_API_KEY, CLOUDFLARE_API_KEY, OPENROUTER_API_KEY]):
    st.error("🔑 **No AI provider keys found.**")
    st.info(
        "Add at least one to Streamlit Secrets:\n\n"
        "```toml\n"
        "CEREBRAS_API_KEY = \"csk-...\"\n"
        "CLOUDFLARE_API_KEY = \"...\"\n"
        "CLOUDFLARE_ACCOUNT_ID = \"...\"\n"
        "OPENROUTER_API_KEY = \"sk-or-v1-...\"\n"
        "```"
    )
    st.stop()

# ============================================================
# FILES
# ============================================================

DOCUMENTS_DIR = Path("documents")
DOCUMENTS_DIR.mkdir(exist_ok=True)
HISTORY_FILE = Path("chat_history.json")

# ============================================================
# PROVIDERS
# ============================================================

cerebras_client = Cerebras(api_key=CEREBRAS_API_KEY) if CEREBRAS_API_KEY else None


def _chat_cerebras(messages, max_tokens, temperature):
    response = cerebras_client.chat.completions.create(
        model="llama3.1-8b",
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content


def _chat_cloudflare(messages, max_tokens, temperature):
    if not CLOUDFLARE_API_KEY or not CLOUDFLARE_ACCOUNT_ID:
        raise Exception("Cloudflare not configured")

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/meta/llama-3.1-8b-instruct"
    )
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {CLOUDFLARE_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["result"]["response"]


def _chat_openrouter(messages, max_tokens, temperature):
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def chat_with_fallback(messages, max_tokens=1000, temperature=0.3):
    providers = []
    if cerebras_client:
        providers.append(("Cerebras", _chat_cerebras))
    if CLOUDFLARE_API_KEY and CLOUDFLARE_ACCOUNT_ID:
        providers.append(("Cloudflare", _chat_cloudflare))
    if OPENROUTER_API_KEY:
        providers.append(("OpenRouter", _chat_openrouter))

    last_error = None
    for name, func in providers:
        try:
            result = func(messages, max_tokens, temperature)
            if result and result.strip():
                return result, name
        except Exception as e:
            last_error = f"{name}: {e}"
            continue

    raise Exception(f"All providers failed. Last error: {last_error}")

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
    # Brand with logo
    st.markdown(
        f"""
        <div class="side-logo">
            <img src="{ICON_DATA_URI}" alt="Nexus AI" />
            <div>
                <div class="side-logo-text">Nexus AI</div>
                <div class="side-logo-sub">INTELLIGENT ASSISTANT</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

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

    st.markdown("---")

    active = []
    if CEREBRAS_API_KEY: active.append("Cerebras")
    if CLOUDFLARE_API_KEY and CLOUDFLARE_ACCOUNT_ID: active.append("Cloudflare")
    if OPENROUTER_API_KEY: active.append("OpenRouter")
    st.caption(f"🔗 Providers: {', '.join(active) if active else 'None'}")

# ============================================================
# MAIN PAGE
# ============================================================

current_chat = st.session_state.current_chat
messages = st.session_state.chats[current_chat]

# Big atom logo header
st.markdown(
    f"""
    <div class="nexus-header">
        <img src="{LOGO_DATA_URI}" alt="Nexus AI logo" />
    </div>
    """,
    unsafe_allow_html=True,
)

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

                answer, used_provider = chat_with_fallback(
                    api_messages,
                    max_tokens=1000,
                    temperature=0.3,
                )
                answer = clean_response(answer)

                if not answer:
                    answer = "I couldn't generate a final answer. Please try again."

                st.markdown(answer)
                st.caption(f"⚡ Response via {used_provider}")
                messages.append({"role": "assistant", "content": answer})
                save_chats()

            except Exception as e:
                st.error("⚠️ All providers failed. Please try again.")
                st.code(str(e))

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.markdown(
    f"""
    <div style="display:flex; align-items:center; justify-content:center; gap:0.5rem; padding: 0.5rem 0;">
        <img src="{ICON_DATA_URI}" style="width:18px; height:18px; border-radius:5px; opacity:0.85;" />
        <span style="color:#667eea; font-size:0.85rem;">Nexus AI · Your intelligent assistant</span>
    </div>
    """,
    unsafe_allow_html=True
)
