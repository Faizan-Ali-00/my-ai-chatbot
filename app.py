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
    st.info(
        "Go to Manage app → Settings → Secrets "
        "and add HF_TOKEN."
    )
    st.stop()


# ============================================================
# MODEL
# ============================================================

try:
    MODEL_NAME = st.secrets["MODEL_NAME"]
except Exception:
    MODEL_NAME = "openai/gpt-oss-120b"


# ============================================================
# DOCUMENTS
# ============================================================

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
    "A simple AI assistant with conversation and PDF support."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Settings")

    st.write("Current model:")
    st.code(MODEL_NAME)

    st.divider()

    if st.button("🗑️ Clear Chat"):

        st.session_state.messages = []

        st.rerun()


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


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

            documents.append({
                "name": file.name,
                "text": text
            })

    return documents


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
        f"{best_document['text'][:4000]}"
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


# ============================================================
# PROCESS MESSAGE
# ============================================================

if prompt:

    # --------------------------------------------------------
    # USER MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)


    # --------------------------------------------------------
    # AI MESSAGE
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:

                # Only keep the most recent conversation
                recent_messages = (
                    st.session_state.messages[-4:]
                )

                # Find relevant PDF information
                context = find_relevant_context(prompt)


                # ------------------------------------------------
                # SYSTEM PROMPT
                # ------------------------------------------------

                system_prompt = """
You are a helpful AI assistant.

Answer the user's question clearly and directly.

For simple questions, answer directly.

For complicated questions, explain step by step.

Do not unnecessarily repeat the user's question.

If relevant document information is provided,
use it when answering.

Do not invent information from documents.

If the answer cannot be found in the document,
say that clearly.
"""


                if context:

                    system_prompt += f"""

Relevant document information:

{context}
"""


                # ------------------------------------------------
                # CREATE MESSAGES
                # ------------------------------------------------

                messages = [
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ]

                messages.extend(recent_messages)


                # ------------------------------------------------
                # HUGGING FACE REQUEST
                # ------------------------------------------------

                response = client.chat_completion(

                    model=MODEL_NAME,

                    messages=messages,

                    max_tokens=200,

                    temperature=0.7
                )


                # ------------------------------------------------
                # EXTRACT RESPONSE
                # ------------------------------------------------

                answer = None

                if response.choices:

                    message = response.choices[0].message

                    # Normal response
                    if hasattr(message, "content"):
                        answer = message.content

                    # Some models/providers may return
                    # reasoning separately.
                    if not answer and hasattr(
                        message,
                        "reasoning_content"
                    ):
                        answer = message.reasoning_content


                # ------------------------------------------------
                # CHECK RESPONSE
                # ------------------------------------------------

                if not answer:

                    st.warning(
                        "The model returned no text."
                    )

                    st.code(
                        str(response)
                    )

                    answer = (
                        "I received a response from the model, "
                        "but it contained no readable answer."
                    )


                # ------------------------------------------------
                # DISPLAY
                # ------------------------------------------------

                st.markdown(answer)


                # ------------------------------------------------
                # SAVE ONLY REAL ANSWERS
                # ------------------------------------------------

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })


            except Exception as e:

                st.error(
                    "The AI could not generate a response."
                )

                st.code(str(e))
