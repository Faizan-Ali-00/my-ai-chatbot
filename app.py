from docx import Document
import json
from pathlib import Path

import streamlit as st
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer, util
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
HISTORY_FILE = Path("chat_history.json")
DOCUMENTS_DIR = Path("documents")
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
st.set_page_config(
    page_title="My AI",
    page_icon="🤖",
    layout="wide",
)

def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(
                HISTORY_FILE.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError:
            return {}

    return {}

def save_history(chats):
    HISTORY_FILE.write_text(
        json.dumps(
            chats,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8",
    )
def read_document(file_path):
    try:
        # TXT files
        if file_path.suffix.lower() == ".txt":
            return file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

        # DOCX files
        if file_path.suffix.lower() == ".docx":
            doc = Document(file_path)

            text = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text)

            return "\n".join(text)

        # PDF files
        if file_path.suffix.lower() == ".pdf":
            reader = PdfReader(file_path)

            text = []

            for page in reader.pages:
                page_text = page.extract_text()

                if page_text:
                    text.append(page_text)

            return "\n".join(text)

        # Unsupported file type
        return ""

    except Exception as e:
        print(f"Error reading {file_path.name}: {e}")
        return ""

def split_text(text, chunk_size=700, overlap=100):
    chunks = []
    start = 0

    while start < len(text):
        chunk = text[start:start + chunk_size].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks

@st.cache_resource(show_spinner=False)
def load_document_index():
    document_chunks = []

    if not DOCUMENTS_DIR.exists():
        return None, [], None

    for file_path in DOCUMENTS_DIR.iterdir():
        if file_path.suffix.lower() not in {".pdf", ".txt",".docx"}:
            continue

        text = read_document(file_path)

        for chunk in split_text(text):
            document_chunks.append(
                {
                    "source": file_path.name,
                    "text": chunk,
                }
            )

    if not document_chunks:
        return None, [], None

    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = embedder.encode(
        [chunk["text"] for chunk in document_chunks],
        convert_to_tensor=True,
        normalize_embeddings=True,
    )

    return embedder, document_chunks, embeddings

def search_documents(question):
    embedder, document_chunks, embeddings = load_document_index()

    if not document_chunks:
        return "", []

    question_embedding = embedder.encode(
        question,
        convert_to_tensor=True,
        normalize_embeddings=True,
    )

    matches = util.semantic_search(
        question_embedding,
        embeddings,
        top_k=min(3, len(document_chunks)),
    )[0]

    selected_chunks = []
    sources = []

    for match in matches:
        if match["score"] >= 0.35:
            item = document_chunks[match["corpus_id"]]
            selected_chunks.append(
                f"Source: {item['source']}\n{item['text']}"
            )

            if item["source"] not in sources:
                sources.append(item["source"])

    return "\n\n---\n\n".join(selected_chunks), sources

@st.cache_resource(show_spinner=False)
def load_qwen():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        device_map="cpu",
    )
    model.eval()
    return tokenizer, model

def get_qwen_reply(chat_history, document_context):
    tokenizer, model = load_qwen()

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful, friendly personal AI assistant. "
                "When document context is provided, use it carefully. "
                "If the answer is not in the document context, say so clearly."
            ),
        },
    ]

    if document_context:
        messages.append(
            {
                "role": "system",
                "content": f"DOCUMENT CONTEXT:\n{document_context}",
            }
        )

    messages.extend(chat_history[-12:])

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    model_inputs = tokenizer(
        [prompt],
        return_tensors="pt",
    ).to(model.device)

    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=250,
    )

    new_tokens = generated_ids[:, model_inputs.input_ids.shape[1]:]

    return tokenizer.batch_decode(
        new_tokens,
        skip_special_tokens=True,
    )[0]

if "chats" not in st.session_state:
    st.session_state.chats = load_history()

if not st.session_state.chats:
    st.session_state.chats = {"Chat 1": []}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Chat 1"

if st.session_state.current_chat not in st.session_state.chats:
    st.session_state.current_chat = next(
        iter(st.session_state.chats)
    )

st.session_state.messages = st.session_state.chats[
    st.session_state.current_chat
]

with st.sidebar:
    st.header("My AI")

    if st.button("＋ New Chat", use_container_width=True):
        new_chat_number = len(st.session_state.chats) + 1
        new_chat_name = f"Chat {new_chat_number}"

        st.session_state.chats[new_chat_name] = []
        st.session_state.current_chat = new_chat_name
        st.session_state.messages = st.session_state.chats[new_chat_name]

        save_history(st.session_state.chats)
        st.rerun()

    st.divider()

    st.subheader("💬 Chats")

    for chat_name in st.session_state.chats:
        if st.button(chat_name, use_container_width=True):
            st.session_state.current_chat = chat_name
            st.session_state.messages = st.session_state.chats[chat_name]
            st.rerun()

    st.divider()

    st.subheader("📄 Documents")

    uploaded_file = st.file_uploader(
        "Upload a document",
        type=["pdf", "txt", "docx"],
        key="document_uploader"
    )

    if uploaded_file is not None:
        save_path = DOCUMENTS_DIR / uploaded_file.name
        save_path.write_bytes(uploaded_file.getbuffer())

        load_document_index.clear()

        st.success(f"Uploaded: {uploaded_file.name}")

    document_count = 0

    if DOCUMENTS_DIR.exists():
        document_count = len([
            file_path
            for file_path in DOCUMENTS_DIR.iterdir()
            if file_path.suffix.lower() in {".pdf", ".txt", ".docx"}
        ])

    st.info(f"📚 {document_count} documents ready")

    if st.button("🔄 Reload documents", use_container_width=True):
        load_document_index.clear()
        st.rerun()
st.caption("Your personal AI assistant")
st.divider()
if not st.session_state.messages:
    st.markdown(
        """
        ### 👋 How can I help you?

        Ask me anything, or upload a document and ask questions about its contents.

        **You can upload:**
        - 📄 PDF
        - 📝 TXT
        - 📘 DOCX
        """
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

        if message.get("sources"):
            st.caption("Sources: " + ", ".join(message["sources"]))

user_message = st.chat_input("Message My AI...")

if user_message:
    st.session_state.messages.append(
        {"role": "user", "content": user_message}
    )
    st.session_state.chats[st.session_state.current_chat] = (
    st.session_state.messages
)

    with st.chat_message("user"):
        st.write(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Searching documents and preparing a response..."):
            document_context, sources = search_documents(user_message)
            reply = get_qwen_reply(
                st.session_state.messages,
                document_context,
            )

        st.write(reply)

        if sources:
            st.caption("Sources: " + ", ".join(sources))

    assistant_message = {
        "role": "assistant",
        "content": reply,
        "sources": sources,
    }

    st.session_state.messages.append(assistant_message)

st.session_state.chats[st.session_state.current_chat] = (
    st.session_state.messages
)

save_history(st.session_state.chats)