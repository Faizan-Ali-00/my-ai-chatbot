import streamlit as st
from huggingface_hub import InferenceClient
from pathlib import Path
from pypdf import PdfReader


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="My AI Chatbot",
    page_icon="🤖",
    layout="centered"
)


# ============================================================
# HUGGING FACE TOKEN
# ============================================================

try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
except Exception:
    HF_TOKEN = None

if not HF_TOKEN:
    st.error("Hugging Face token not found.")
    st.info("Go to Manage app → Settings → Secrets and add HF_TOKEN.")
    st.stop()


# ============================================================
# MODEL
# ============================================================

MODEL_NAME = "google/gemma-2-2b-it"

DOCUMENTS_DIR = Path("documents")
DOCUMENTS_DIR.mkdir(exist_ok=True)


# ============================================================
# HUGGING FACE CLIENT
# ============================================================

@st.cache_resource
def get_client():

    return InferenceClient(
        api_key=HF_TOKEN
    )


client = get_client()


# ============================================================
# PAGE
# ============================================================

st.title("🤖 My AI Chatbot")

st.caption(
    "Ask questions, chat with AI, and ask questions about your documents."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Settings")

    st.write("Model")

    st.code(MODEL_NAME)

    if st.button("🗑️ Clear Chat"):

        st.session_state.messages = []

        st.rerun()


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# ============================================================
# PDF READER
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


# ============================================================
# LOAD PDF DOCUMENTS
# ============================================================

def load_documents():

    documents = []

    for file in DOCUMENTS_DIR.glob("*.pdf"):

        text = extract_pdf_text(file)

        if text.strip():

            documents.append({
                "name": file.name,
                "text": text
            })

    return documents


# ============================================================
# FIND DOCUMENT CONTEXT
# ============================================================

def find_relevant_context(question):

    documents = load_documents()

    if not documents:

        return ""

    question_words = set(
        question.lower().split()
    )

    best_document = None
    best_score = 0

    for document in documents:

        document_words = set(
            document["text"].lower().split()
        )

        score = len(
            question_words.intersection(document_words)
        )

        if score > best_score:

            best_score = score
            best_document = document

    if best_document is None:

        return ""

    return (
        f"Document: {best_document['name']}\n\n"
        f"{best_document['text'][:5000]}"
    )


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input("Ask me anything...")


if prompt:

    # ========================================================
    # USER MESSAGE
    # ========================================================

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):

        st.markdown(prompt)


    # ========================================================
    # AI RESPONSE
    # ========================================================

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:

                # Keep only recent messages
                recent_messages = (
                    st.session_state.messages[-6:]
                )


                # Get PDF information
                context = find_relevant_context(prompt)


                # =================================================
                # SYSTEM PROMPT
                # =================================================

                system_prompt = """
You are a helpful AI assistant.

Answer clearly and directly.

For simple questions, give a concise answer.

For complicated questions, explain step by step.

Do not unnecessarily repeat the user's question.

If document information is provided, use it when relevant.

Do not invent information from documents.

If you don't know something, say so.
"""


                if context:

                    system_prompt += f"""

Relevant document information:

{context}
"""


                # =================================================
                # CREATE MESSAGES
                # =================================================

                messages = [

                    {
                        "role": "system",
                        "content": system_prompt
                    }

                ]

                messages.extend(recent_messages)


                # =================================================
                # CALL HUGGING FACE
                # =================================================

                response = client.chat_completion(

                    model=MODEL_NAME,

                    messages=messages,

                    max_tokens=200,

                    temperature=0.7

                )


                # =================================================
                # GET ANSWER
                # =================================================

                answer = (
                    response.choices[0]
                    .message
                    .content
                )


                # =================================================
                # DISPLAY ANSWER
                # =================================================

                st.markdown(answer)


                # =================================================
                # SAVE ANSWER
                # =================================================

                st.session_state.messages.append({

                    "role": "assistant",

                    "content": answer

                })


            except Exception as e:

                st.error(
                    "The AI could not generate a response."
                )

                st.code(str(e))
