# LPU RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot for LPU college that allows secure document management and interactive Q&A.

## Features

- Secure admin interface (accessed via `/?admin=true`)
- Support for multiple document types (PDF, Markdown, JSON)
- Batch folder processing
- Clean user chat interface
- Built with Streamlit and ChromaDB

## Setup in Streamlit Cloud

1. Fork this repository
2. Set up Streamlit deployment
3. Configure the following environment variables:
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

4. Add the following secrets in Streamlit settings:
   ```
   # Get an API key from: https://makersuite.google.com/
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

## Admin Access

1. Access admin panel: `your-app-url/?admin=true`
2. Login credentials:
   - Username: `admin`
   - Password: `admin123`

## File Support

The chatbot can process:
- PDF documents
- Markdown files (.md)
- JSON files

## Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Important Files for Deployment

- `packages.txt`: System dependencies for Streamlit Cloud
- `requirements.txt`: Python package dependencies
- `.streamlit/config.toml`: Streamlit configuration
- `app.py`: Main application code

## Note

Make sure to keep your admin credentials secure and change them in production. The admin interface is hidden from regular users and only accessible through the direct URL parameter.
