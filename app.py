import streamlit as st
from huggingface_hub import InferenceClient
from pathlib import Path
from pypdf import PdfReader
import json


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
# FILES
# ============================================================

DOCUMENTS_DIR = Path("documents")
DOCUMENTS_DIR.mkdir(exist_ok=True)

HISTORY_FILE = Path("chat_history.json")


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
# LOAD CHATS FROM FILE
# ============================================================

def load_chats():

    if not HISTORY_FILE.exists():

        return {
            "New Chat": []
        }


    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            chats = json.load(file)


        if not chats:

            return {
                "New Chat": []
            }


        return chats


    except Exception:

        return {
            "New Chat": []
        }


# ============================================================
# SAVE CHATS TO FILE
# ============================================================

def save_chats():

    try:

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                st.session_state.chats,
                file,
                indent=2,
                ensure_ascii=False
            )


    except Exception as e:

        st.error(
            f"Could not save chats: {e}"
        )


# ============================================================
# CHAT SESSION
# ============================================================

if "chats" not in st.session_state:

    st.session_state.chats = load_chats()


if "current_chat" not in st.session_state:

    st.session_state.current_chat = (
        list(st.session_state.chats.keys())[0]
    )


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


# ============================================================
# LOAD DOCUMENTS
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
# FIND RELEVANT PDF CONTEXT
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
            question_words.intersection(
                document_words
            )
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
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("💬 Chats")


    # --------------------------------------------------------
    # NEW CHAT
    # --------------------------------------------------------

    if st.button(
        "➕ New Chat",
        use_container_width=True
    ):

        create_new_chat()

        st.rerun()


    st.divider()


    # --------------------------------------------------------
    # CHAT LIST
    # --------------------------------------------------------

    chat_names = list(
        st.session_state.chats.keys()
    )


    for chat_name in chat_names:

        is_current = (

            chat_name
            == st.session_state.current_chat

        )


        if is_current:

            button_text = "▶ " + chat_name

        else:

            button_text = chat_name


        if st.button(
            button_text,
            key=f"chat_{chat_name}",
            use_container_width=True
        ):

            st.session_state.current_chat = (
                chat_name
            )

            st.rerun()


    st.divider()


    # --------------------------------------------------------
    # DELETE CURRENT CHAT
    # --------------------------------------------------------

    if st.button(
        "🗑️ Delete Current Chat",
        use_container_width=True
    ):

        current = (
            st.session_state.current_chat
        )


        if len(st.session_state.chats) > 1:

            del st.session_state.chats[current]


            st.session_state.current_chat = (
                list(
                    st.session_state.chats.keys()
                )[0]
            )


        else:

            st.session_state.chats[current] = []


        # IMPORTANT:
        # Save BEFORE rerun.

        save_chats()

        st.rerun()


# ============================================================
# CURRENT CHAT
# ============================================================

current_chat = (
    st.session_state.current_chat
)


messages = (
    st.session_state.chats[current_chat]
)


# ============================================================
# PAGE TITLE
# ============================================================

st.title("🤖 My AI Chatbot")

st.caption(
    f"Current chat: {current_chat}"
)


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input(
    "Ask me anything..."
)


# ============================================================
# PROCESS MESSAGE
# ============================================================

if prompt:


    # --------------------------------------------------------
    # USER MESSAGE
    # --------------------------------------------------------

    messages.append({

        "role": "user",

        "content": prompt

    })


    # --------------------------------------------------------
    # AUTOMATIC CHAT TITLE
    # --------------------------------------------------------

    if current_chat.startswith("New Chat"):

        words = prompt.split()


        if len(words) > 6:

            title = (
                " ".join(words[:6])
                + "..."
            )

        else:

            title = prompt


        title = title[:40]


        # Prevent duplicate chat names

        original_title = title

        number = 2


        while (
            title in st.session_state.chats
            and title != current_chat
        ):

            title = (
                f"{original_title} {number}"
            )

            number += 1


        if title != current_chat:

            st.session_state.chats[title] = (
                messages
            )


            del st.session_state.chats[
                current_chat
            ]


            st.session_state.current_chat = (
                title
            )


            current_chat = title

            messages = (
                st.session_state.chats[title]
            )


            save_chats()


    # --------------------------------------------------------
    # DISPLAY USER MESSAGE
    # --------------------------------------------------------

    with st.chat_message("user"):

        st.markdown(prompt)


    # --------------------------------------------------------
    # AI RESPONSE
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:


                # ----------------------------------------------
                # KEEP RECENT CONVERSATION
                # ----------------------------------------------

                recent_messages = (
                    messages[-4:]
                )


                # ----------------------------------------------
                # PDF CONTEXT
                # ----------------------------------------------

                context = (
                    find_relevant_context(prompt)
                )


                # ----------------------------------------------
                # SYSTEM PROMPT
                # ----------------------------------------------

                system_prompt = """

You are a helpful AI assistant.

Answer the user's question clearly
and directly.

For simple questions, answer directly.

For complicated questions,
explain step by step.

Do not unnecessarily repeat
the user's question.

If relevant document information
is provided, use it when answering.

Do not invent information from documents.

If the answer cannot be found in
the document, say that clearly.

Do not reveal internal reasoning.
"""


                if context:

                    system_prompt += f"""

Relevant document information:

{context}
"""


                # ----------------------------------------------
                # API MESSAGES
                # ----------------------------------------------

                api_messages = [

                    {

                        "role": "system",

                        "content": system_prompt

                    }

                ]


                api_messages.extend(
                    recent_messages
                )


                # ----------------------------------------------
                # HUGGING FACE REQUEST
                # ----------------------------------------------

                response = client.chat_completion(

                    model=MODEL_NAME,

                    messages=api_messages,

                    max_tokens=7000,

                    temperature=0.7

                )


                # ----------------------------------------------
                # GET FINAL ANSWER
                # ----------------------------------------------

                answer = None


                if response.choices:

                    message = (
                        response.choices[0].message
                    )


                    answer = getattr(
                        message,
                        "content",
                        None
                    )


                # ----------------------------------------------
                # CHECK ANSWER
                # ----------------------------------------------

                if not answer:

                    answer = (

                        "I couldn't generate "
                        "a final answer. "
                        "Please try again."

                    )


                # ----------------------------------------------
                # DISPLAY ANSWER
                # ----------------------------------------------

                st.markdown(answer)


                # ----------------------------------------------
                # SAVE ANSWER
                # ----------------------------------------------

                messages.append({

                    "role": "assistant",

                    "content": answer

                })


                # ----------------------------------------------
                # SAVE ENTIRE CHAT
                # ----------------------------------------------

                save_chats()


            except Exception as e:

                st.error(
                    "The AI could not generate a response."
                )

                st.code(
                    str(e)
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🤖 My AI Chatbot"
)
