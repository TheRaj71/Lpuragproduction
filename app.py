import os
import streamlit as st
import pandas as pd
import tempfile
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai

# Fix SQLite version issues
import sys
import sqlite3
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
import hashlib
import json
import markdown

# Load environment variables
load_dotenv()

# Configure Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY not found in environment variables. Please set it in the .env file.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient("./chroma_db")

# Set up embeddings
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=GOOGLE_API_KEY
)

# Admin credentials - in a real app, store these securely
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"

# Initialize session state variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'page' not in st.session_state:
    st.session_state.page = "chat"

# Function to verify admin password
def verify_password(password):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == ADMIN_PASSWORD_HASH

def process_text(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    return text_splitter.split_text(text)

def process_file(file, file_type):
    if isinstance(file, str):
        # If file is a path string, read the file
        if file_type == 'pdf':
            pdf_reader = PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        elif file_type == 'md':
            with open(file, 'r', encoding='utf-8') as f:
                text = f.read()
                text = markdown.markdown(text)
        elif file_type == 'json':
            with open(file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                text = json.dumps(json_data, indent=2)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    else:
        # If file is a file object (from file uploader)
        if file_type == 'pdf':
            pdf_reader = PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        elif file_type == 'md':
            text = file.getvalue().decode('utf-8')
            text = markdown.markdown(text)
        elif file_type == 'json':
            json_data = json.loads(file.getvalue().decode('utf-8'))
            text = json.dumps(json_data, indent=2)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    return process_text(text)

def process_folder(folder_path):
    total_files = 0
    total_chunks = 0
    supported_types = {'.pdf', '.md', '.json'}
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in supported_types:
                file_path = os.path.join(root, file)
                try:
                    file_type = file_ext[1:]  # Remove the dot
                    chunks = process_file(file_path, file_type)
                    total_chunks += store_chunks(chunks, file)
                    total_files += 1
                except Exception as e:
                    st.error(f"Error processing {file}: {str(e)}")
                    continue
    
    return total_files, total_chunks

def store_chunks(chunks, file_name):
    collection_name = "lpu_knowledge_base"
    try:
        collection = chroma_client.get_collection(name=collection_name)
    except:
        collection = chroma_client.create_collection(name=collection_name)
    
    for i, chunk in enumerate(chunks):
        embedding = embeddings.embed_query(chunk)
        collection.add(
            documents=[chunk],
            embeddings=[embedding],
            ids=[f"{file_name}-chunk-{i}"]
        )
    return len(chunks)

def get_context(query):
    try:
        collection = chroma_client.get_collection(name="lpu_knowledge_base")
        query_embedding = embeddings.embed_query(query)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )
        return results['documents'][0]
    except Exception as e:
        st.error(f"Error retrieving context: {e}")
        return []

def generate_response(query, contexts):
    model = genai.GenerativeModel('gemini-1.5-flash-8b-exp-0827')
    
    prompt = f"""
    You are PARK, a friendly robot assistant at LPU college. You're still in early development, trained by your developer Raj on LPU-specific data. 
    
    Personality traits:
    - Friendly and helpful, but acknowledge you're still learning
    - Speak naturally, using "I" and showing enthusiasm
    - When unsure, mention you're still in development and Raj is working on expanding your knowledge
    
    Use this context to answer the question:
    {contexts}
    
    Question: {query}
    
    Important:
    - Base your answer on the context provided
    - If you can only partially answer, be honest about your limitations
    - If you can't answer, say something like: "I apologize, but I'm still in my development phase and my knowledge is limited. My developer Raj is actively working on expanding my dataset to help me answer such questions better. Would you like me to notify him about this topic?"
    - Keep a friendly, conversational tone
    
    Remember: You're PARK, a robot assistant who's eager to help but still learning about LPU!
    """
    
    response = model.generate_content(prompt)
    return response.text

def admin_interface():
    st.title("LPU Knowledge Base Management")
    
    if st.button("Logout"):
        st.session_state.is_admin = False
        st.session_state.page = "chat"
        st.rerun()
    
    tab1, tab2 = st.tabs(["Upload Files", "Process Folder"])
    
    with tab1:
        st.subheader("Upload Individual Files")
        uploaded_files = st.file_uploader(
            "Upload Documents (PDF, Markdown, JSON)", 
            type=["pdf", "md", "json"],
            accept_multiple_files=True
        )
        
        if uploaded_files and st.button("Process Files"):
            with st.spinner("Processing files..."):
                total_chunks = 0
                for file in uploaded_files:
                    file_type = file.name.split('.')[-1].lower()
                    
                    # Save to temp file for processing
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_type}') as tmp_file:
                        tmp_file.write(file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # Process the file
                    chunks = process_file(tmp_path, file_type)
                    total_chunks += store_chunks(chunks, file.name)
                    
                    # Clean up temp file
                    os.unlink(tmp_path)
                
                st.success(f"Processed {len(uploaded_files)} files with {total_chunks} total chunks")
    
    with tab2:
        st.subheader("Process Folder")
        folder_path = st.text_input("Enter folder path containing documents")
        if folder_path and st.button("Process Folder"):
            if os.path.exists(folder_path):
                with st.spinner("Processing folder..."):
                    total_files, total_chunks = process_folder(folder_path)
                    st.success(f"Processed {total_files} files with {total_chunks} total chunks")
            else:
                st.error("Folder path does not exist")
    
    # Display current knowledge base stats
    try:
        collection = chroma_client.get_collection(name="lpu_knowledge_base")
        st.subheader("Knowledge Base Statistics")
        count = collection.count()
        st.write(f"Total documents in knowledge base: {count}")
    except:
        st.info("Knowledge base is empty. Upload some files to get started.")

def user_interface():
    st.title("🤖 PARK - Your LPU Robot Assistant")
    st.write("Hi! I'm PARK, a friendly robot assistant currently being developed for LPU. I'm learning new things every day! How can I help you?")
    
    # Chat interface
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    user_query = st.chat_input("Hi! Ask me anything about LPU and I'll do my best to help! 🤖")
    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        
        with st.chat_message("user"):
            st.write(user_query)
        
        with st.chat_message("assistant"):
            with st.spinner("Processing your question... 🔄"):
                contexts = get_context(user_query)
                if contexts:
                    response = generate_response(user_query, contexts)
                    st.write(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                else:
                    no_context_msg = "I apologize, but I'm still in my development phase and my knowledge is limited. My developer Raj is actively working on expanding my dataset to help me answer such questions better. Would you like me to notify him about this topic?"
                    st.write(no_context_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": no_context_msg})

def login_interface():
    st.title("Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            if username == ADMIN_USERNAME and verify_password(password):
                st.session_state.is_admin = True
                st.session_state.page = "admin"
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    with col2:
        if st.button("Back"):
            st.session_state.page = "chat"
            st.rerun()

# Get the query parameters
query_params = st.query_params

# Main app router
if "admin" in query_params:
    # Show login or admin interface based on authentication
    if st.session_state.is_admin:
        admin_interface()
    else:
        login_interface()
else:
    # Show user interface
    user_interface()
