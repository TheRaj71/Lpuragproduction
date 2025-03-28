# Domain-Specific RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that allows you to create specialized knowledge domains from PDF documents and chat with an AI assistant that answers questions based on that knowledge.

## Features

- Create multiple knowledge domains
- Upload and process PDF documents for each domain
- Chat with an AI assistant that answers questions based on the domain knowledge
- RAG implementation with Google's Gemini API and ChromaDB for vector storage

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with the following variables:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   DOMAIN_CONFIG_PATH=./data/domain_config.json
   UPLOAD_FOLDER=./data/uploads
   ```
4. Get a Google API key for Gemini from [Google AI Studio](https://makersuite.google.com/)

## Usage

1. Run the application:
   ```
   streamlit run app.py
   ```
2. In the sidebar, use the "Admin: Manage Domains" section to:
   - Create a new knowledge domain
   - Upload PDF documents to a domain
3. Select a domain to chat with from the "Select Domain for Chat" section
4. Start asking questions in the chat interface

## How it Works

1. PDF documents are processed and split into chunks
2. Each chunk is embedded using Google's embedding model
3. Embeddings are stored in ChromaDB collections (one per domain)
4. When you ask a question, the system:
   - Embeds your question
   - Retrieves the most relevant chunks from the domain's collection
   - Sends the question and relevant context to Gemini to generate a response

## Requirements

- Python 3.8+
- See requirements.txt for all dependencies