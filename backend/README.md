# Backend for Responsive Chat Application

This is the backend service for the responsive chat application. It provides:
- LLM integration with Ollama
- Document processing
- Chat functionality
- Memory management

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the Ollama server:
```bash
cd ollama
./ollama.exe serve
```

4. Run the Flask server:
```bash
cd app
python chatbot.py
```

## Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── chatbot.py      # Main chatbot logic
│   ├── routes.py       # API routes
│   ├── llm_integration.py  # Ollama integration
│   ├── uploads/        # Uploaded files
│   ├── chats/         # Chat history
│   ├── documents/     # Processed documents
│   └── links/         # Crawled links
├── ollama/            # Ollama executable and models
│   └── ollama.exe     # Ollama server executable
└── requirements.txt   # Python dependencies
```

## API Endpoints

- POST `/chat` - Send a message to the chatbot
- POST `/document_upload` - Upload a document
- GET `/documents` - List uploaded documents
- POST `/link_upload` - Process a URL
- GET `/links` - List processed links

## Models

The application uses two Ollama models:
- `llama3.2:1B` - For simple responses
- `deepseek-r1:1.5b` - For reasoned responses 