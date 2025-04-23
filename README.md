# 🚀 Chatverket

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/React-18.2.0-blue.svg" alt="React Version">
  <img src="https://img.shields.io/badge/TypeScript-5.0.0-blue.svg" alt="TypeScript Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</div>

A modern, responsive chatbot with memory and document processing capabilities, built with a service-based architecture and LLM integration. Features a beautiful React frontend and a powerful Python backend.

## ✨ Features

### 🤖 Advanced Chat Functionality
- LLM-powered responses with streaming support
- Context-aware conversations
- Multiple model types (SIMPLE and REASONED)
- Customizable model parameters
- Real-time typing indicators
- Markdown support for responses

### 📄 Document Processing
- Support for PDF, TXT, JSON, DOCX
- Content extraction and indexing
- Document context integration
- Metadata management
- File previews and thumbnails
- Drag-and-drop upload support

### 🌐 Web Integration
- Web page content extraction
- Link processing and storage
- Rich link previews
- Domain analytics
- Automatic content summarization
- Metadata extraction

### 🧠 Memory System
- Semantic search capabilities
- Conversation history management
- Context-aware memory retrieval
- Memory persistence
- Smart context switching
- Long-term memory storage

### 🏗️ Service Architecture
- Modular service-based design
- LLM Integration Service
- Memory Service
- Analytics Service
- Document Processing Service
- Event-driven architecture

### 📚 API & Documentation
- RESTful API with Swagger/OpenAPI docs
- Comprehensive internal documentation
- Interactive API documentation
- TypeScript/Type definitions
- Auto-generated API clients
- Detailed error handling

### 🎨 Frontend Features
- Modern, responsive UI
- Real-time updates
- Dark/Light mode support
- Customizable themes
- Mobile-first design
- Progressive Web App (PWA) support

## 🏗️ Architecture

```
chatverket/
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # Frontend services
│   │   ├── hooks/           # Custom React hooks
│   │   ├── types/           # TypeScript types
│   │   └── styles/          # CSS and themes
│   └── public/              # Static assets
├── backend/                  # Python backend
│   ├── app/
│   │   ├── services/        # Service implementations
│   │   │   ├── llm_integration.py
│   │   │   ├── memory_service.py
│   │   │   ├── analytics_service.py
│   │   │   └── swagger_config.py
│   │   ├── chatbot.py       # Main application
│   │   └── api_docs.py      # API specifications
│   └── tests/               # Test suite
├── docs/                    # Internal documentation
│   ├── api/                 # API documentation
│   ├── components/          # Component documentation
│   └── data-models/         # Data model documentation
└── README.md                # This file
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+
- Ollama (for LLM integration)
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/chatverket.git
cd chatverket
```

2. Install backend dependencies:
```bash
pip install -e .
pip install -r backend/tests/requirements-test.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

4. Start Ollama (required for LLM integration):
```bash
ollama serve
```

### Running the Application

1. Start the backend server:
```bash
python -m backend.app.chatbot
```

2. Start the frontend development server:
```bash
cd frontend
npm run dev
```

3. Access the application:
   - Frontend: `http://localhost:3000`
   - API Base URL: `http://localhost:5000`
   - Swagger UI: `http://localhost:5000/docs`
   - ReDoc: `http://localhost:5000/redoc`

## 📚 Documentation

### API Documentation
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI Spec: `/apispec.json`

### Internal Documentation
- API Endpoints: `docs/api/`
- Components: `docs/components/`
- Data Models: `docs/data-models/`

### Key Endpoints
- `POST /chat`: Main chat endpoint with LLM integration
- `GET /documents`: List uploaded documents
- `GET /links`: List processed links
- `POST /document_upload`: Upload a document
- `POST /link_upload`: Process a web link
- `POST /store_memory`: Store conversation memory
- `POST /retrieve_memory`: Retrieve relevant memories
- `GET /analytics/*`: Various analytics endpoints

## 💻 Development

### Frontend Development
- Built with React 18 and TypeScript
- Uses Tailwind CSS for styling
- Implements modern React patterns
- Custom hooks for API integration
- Responsive design system
- Component library

### Backend Services
1. **LLM Integration Service**
   - Handles model interactions
   - Manages conversation history
   - Provides streaming support

2. **Memory Service**
   - Manages conversation memory
   - Implements semantic search
   - Handles memory persistence

3. **Analytics Service**
   - Tracks usage metrics
   - Provides performance insights
   - Generates usage reports

4. **Document Processing Service**
   - Handles file uploads
   - Extracts content
   - Manages metadata

### Testing
```bash
# Backend tests
pytest backend/tests/test_chat_api.py -v

# Frontend tests
cd frontend
npm test
```

## 📦 Requirements

### Backend
- Python 3.8+
- Ollama running locally
- See `setup.py` for Python package dependencies

### Frontend
- Node.js 18+
- npm or yarn
- Modern web browser

## 📄 License

MIT License - see [LICENSE](LICENSE) for details
