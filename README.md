# 🤖 My AI Chatbot

A personal AI chatbot built with Streamlit, Qwen, and RAG for document-based question answering.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Qwen](https://img.shields.io/badge/Qwen-2.5%201.5B-6E4AFF?logo=alibabacloud&logoColor=white)
![RAG](https://img.shields.io/badge/RAG-Enabled-success)
![License](https://img.shields.io/badge/License-MIT-green)

## 📖 Overview

My AI Chatbot is a personal assistant that combines conversational AI with Retrieval-Augmented Generation (RAG). It can chat naturally, and when you upload documents, it answers your questions grounded in their content — not just general knowledge.

## ✨ Features

- 💬 Chat with an AI assistant
- 🧠 Powered by Qwen 2.5 1.5B
- 📄 Upload PDF, TXT, and DOCX documents
- 🔍 Semantic document search using embeddings
- 📚 Ask questions about uploaded documents
- 💾 Chat history saved locally

## 🛠️ Tech Stack

- Frontend: Streamlit
- LLM: Qwen 2.5 1.5B
- RAG: Embeddings + semantic search
- Language: Python 3.10+
- Storage: Local JSON (chat history)

## 📂 Project Structure

    my-ai-chatbot/
    ├── app.py                # Streamlit app (main entry point)
    ├── chat_history.json     # Local chat storage
    ├── requirements.txt      # Python dependencies
    ├── LICENSE               # MIT License
    ├── .gitignore            # Git ignore rules
    └── README.md

## ⚙️ Installation

### 1. Clone the repository

    git clone https://github.com/Faizan-Ali-00/my-ai-chatbot.git
    cd my-ai-chatbot

### 2. Create a virtual environment

    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate

### 3. Install dependencies

    pip install -r requirements.txt

## ▶️ Usage

Run the Streamlit app:

    streamlit run app.py

Then open your browser at http://localhost:8501

1. Type a message to chat with the assistant
2. Upload a PDF, TXT, or DOCX file
3. Ask questions about the uploaded document
4. Chat history is saved locally

## 🔒 Notes

- Chat history is stored locally in `chat_history.json`
- No API keys required for the local Qwen 2.5 1.5B model
- If you add external APIs later, never commit `.env` files

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m "Add some AmazingFeature"`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License — see the LICENSE file for details.

## 👤 Author

Faizan Ali

- GitHub: https://github.com/Faizan-Ali-00
- Repository: https://github.com/Faizan-Ali-00/my-ai-chatbot

## ⭐ Show Your Support

If this project helped you, please give it a star on GitHub.

## 🙏 Acknowledgments

- Qwen — https://github.com/QwenLM/Qwen
- Streamlit — https://streamlit.io
- Open-source contributors
