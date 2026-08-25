import streamlit as st
from huggingface_hub import InferenceClient
from pathlib import Path
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer, util


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="My AI Chatbot",
    page_icon="🤖",
    layout="centered"
)


# ============================================================
# SECRETS
# ============================================================

try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
except Exception:
    HF_TOKEN = None

if not HF_TOKEN:
    st.error(
        "Hugging Face token not found.\n\n"
        "Go to Streamlit Cloud → Settings → Secrets "
        "and add HF_TOKEN."
    )
    st.stop()


# ============================================================
# MODEL
# ============================================================

# You can change this later from Streamlit Secrets
# without changing this Python file.

try:
    MODEL_NAME = st.secrets["MODEL_NAME"]
except Exception:
    MODEL_NAME = "google/gemma-3-1b-it"


# ============================================================
# DIRECTORIES
# ============================================================

DOCUMENTS_DIR = Path("documents")
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
# TITLE
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

    st.write("Model:")
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
# PDF TEXT EXTRACTION
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

            documents.append(
                {
                    "name": file.name,
                    "text": text
                }
            )

    return documents


# ============================================================
# FIND RELEVANT DOCUMENT CONTEXT
# ============================================================

def find_relevant_context(question):

    documents = load_documents()

    if not documents:

        return ""

    texts = [
        document["text"]
        for document in documents
    ]

    try:

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

    except Exception:

        return ""


# ============================================================
# DISPLAY PREVIOUS MESSAGES
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


# ============================================================
# PROCESS QUESTION
# ============================================================

if prompt:

    # --------------------------------------------------------
    # SHOW USER MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("user"):

        st.markdown(prompt)


    # --------------------------------------------------------
    # AI RESPONSE
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:

                # Keep only recent messages.
                # This reduces unnecessary input.
                recent_messages = (
                    st.session_state.messages[-6:]
                )


                # ------------------------------------------------
                # DOCUMENT SEARCH
                # ------------------------------------------------

                context = find_relevant_context(prompt)


                # ------------------------------------------------
                # SYSTEM INSTRUCTION
                # ------------------------------------------------

                system_prompt = """
You are a helpful AI assistant.

Answer the user's question clearly and directly.

For simple questions, give a simple answer.

For complex questions, explain the important points.

Do not unnecessarily repeat the user's question.

If relevant document information is provided,
use that information in your answer.

Do not invent facts from documents.

If the requested information cannot be found
in the provided documents, say so clearly.
"""


                if context:

                    system_prompt += f"""

Relevant document information:

{context}
"""


                # ------------------------------------------------
                # BUILD MESSAGE LIST
                # ------------------------------------------------

                messages = [
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ]

                messages.extend(recent_messages)


                # ------------------------------------------------
                # CALL HUGGING FACE
                # ------------------------------------------------

                response = client.chat_completion(

                    model=MODEL_NAME,

                    messages=messages,

                    max_tokens=500,

                    temperature=0.7
                )


                # ------------------------------------------------
                # GET ANSWER
                # ------------------------------------------------

                answer = (
                    response.choices[0]
                    .message
                    .content
                )


                # ------------------------------------------------
                # DISPLAY ANSWER
                # ------------------------------------------------

                st.markdown(answer)


                # ------------------------------------------------
                # SAVE ANSWER
                # ------------------------------------------------

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )


            except Exception as e:

                st.error(
                    "The AI could not generate a response."
                )

                st.code(
                    str(e)
                )
