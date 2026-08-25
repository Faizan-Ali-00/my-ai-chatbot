import streamlit as st
from huggingface_hub import InferenceClient
from pathlib import Path
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer, util


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
    st.error(
        "Hugging Face token not found. "
        "Add HF_TOKEN in Streamlit Secrets."
    )
    st.stop()


# ============================================================
# SETTINGS
# ============================================================

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

DOCUMENTS_DIR = Path("documents")
HISTORY_FILE = Path("chat_history.json")

DOCUMENTS_DIR.mkdir(exist_ok=True)


# ============================================================
# HUGGING FACE CLIENT
# ============================================================

@st.cache_resource
def get_client():
    return InferenceClient(
        provider="auto",
        api_key=HF_TOKEN
    )


client = get_client()


# ============================================================
# EMBEDDING MODEL
# ============================================================

@st.cache_resource
def get_embedding_model():
    return SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )


embedding_model = get_embedding_model()


# ============================================================
# PAGE TITLE
# ============================================================

st.title("🤖 My AI Chatbot")

st.caption(
    "Ask questions, upload documents, and chat with your AI assistant."
)


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

    texts = [
        document["text"]
        for document in documents
    ]

    question_embedding = embedding_model.encode(
        question,
        convert_to_tensor=True
    )

    document_embeddings = embedding_model.encode(
        texts,
        convert_to_tensor=True
    )

    scores = util.cos_sim(
        question_embedding,
        document_embeddings
    )[0]

    best_indices = scores.argsort(
        descending=True
    )[:2]

    context = ""

    for index in best_indices:

        index = int(index)

        context += (
            f"\nDocument: {documents[index]['name']}\n"
            f"{documents[index]['text'][:4000]}\n"
        )

    return context


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input(
    "Ask me anything..."
)


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

                # ------------------------------------------------
                # RECENT CONVERSATION
                # ------------------------------------------------

                recent_messages = (
                    st.session_state.messages[-6:]
                )


                # ------------------------------------------------
                # DOCUMENT CONTEXT
                # ------------------------------------------------

                context = find_relevant_context(prompt)


                # ------------------------------------------------
                # SYSTEM PROMPT
                # ------------------------------------------------

                system_prompt = """
You are a helpful AI assistant.

Give clear, useful, and accurate answers.

Do not unnecessarily repeat the user's question.

For simple questions, answer directly.

For complex questions, explain the answer clearly.

If document context is provided, use it when relevant.

Do not invent information from documents.

If the document does not contain the requested information,
say that the information was not found in the document.
"""


                if context:

                    system_prompt += f"""

Relevant document context:

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
                # GENERATE RESPONSE
                # ------------------------------------------------

                response = client.chat_completion(
                    messages=messages,
                    model=MODEL_NAME,
                    max_tokens=500,
                    temperature=0.7
                )


                # ------------------------------------------------
                # GET ANSWER
                # ------------------------------------------------

                answer = response.choices[0].message.content


                # ------------------------------------------------
                # DISPLAY ANSWER
                # ------------------------------------------------

                st.markdown(answer)


                # ------------------------------------------------
                # SAVE ANSWER
                # ------------------------------------------------

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })


            except Exception as e:

                st.error(
                    "Sorry, I couldn't generate a response."
                )

                st.code(str(e))
