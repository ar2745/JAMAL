# Chatverket

A responsive chatbot with memory and document processing capabilities.

## Features

- Basic chat functionality
- Document processing (PDF, TXT, JSON, DOCX)
- Web page content extraction
- Memory system with semantic search
- Reasoning capabilities
- RESTful API

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/chatverket.git
cd chatverket
```

2. Install the package in development mode:
```bash
pip install -e .
```

3. Install test dependencies:
```bash
pip install -r backend/tests/requirements-test.txt
```

## Usage

1. Start the Flask server:
```bash
python -m backend.app.chatbot
```

2. The API will be available at `http://localhost:5000`

## API Endpoints

- `GET /`: Welcome message
- `POST /chat`: Main chat endpoint
- `GET /documents`: List uploaded documents
- `GET /links`: List processed links
- `POST /document_upload`: Upload a document
- `POST /link_upload`: Process a web link
- `POST /store_memory`: Store conversation memory
- `POST /retrieve_memory`: Retrieve relevant memories

## Testing

Run the test suite:
```bash
pytest backend/tests/test_chat_api.py -v
```

## Requirements

- Python 3.8+
- Ollama running locally (for LLM integration)
- See `setup.py` for Python package dependencies

## License

MIT License
