import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, AsyncGenerator, Dict
from unittest.mock import MagicMock, patch

import aiohttp
import chromadb
import pytest
from fastapi.testclient import TestClient

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.memory import MemoryManager

from backend.app.main import app

# Test configuration
TEST_CONVERSATION_ID = "test_conversation_123"
TEST_DOCUMENT_NAME = "test_document.txt"
TEST_LINK_NAME = "test_link.json"
TEST_EMBEDDING = [0.1] * 768  # Mock embedding vector
CHROMA_COLLECTION_NAME = "test_chat_memories"  # Use a consistent collection name

@pytest.fixture(scope="session")
def test_client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture(scope="session")
def chroma_client() -> chromadb.Client:
    """Create a ChromaDB client for the test session."""
    client = chromadb.Client()
    # Delete existing collection if it exists
    try:
        client.delete_collection(CHROMA_COLLECTION_NAME)
    except ValueError:
        pass  # Collection doesn't exist, which is fine
    # Create fresh collection
    collection = client.create_collection(CHROMA_COLLECTION_NAME)
    return client

@pytest.fixture(autouse=True)
async def setup_and_cleanup(chroma_client: chromadb.Client) -> AsyncGenerator[None, None]:
    """Setup and cleanup for each test."""
    # Setup: Create necessary directories
    os.makedirs('documents', exist_ok=True)
    os.makedirs('links', exist_ok=True)
    
    # Create test document
    with open(os.path.join('documents', TEST_DOCUMENT_NAME), 'w') as f:
        f.write("Test document content")
    
    # Create test link
    with open(os.path.join('links', TEST_LINK_NAME), 'w') as f:
        json.dump({
            "url": "https://example.com",
            "title": "Test Link",
            "content": "Test link content"
        }, f)
    
    # Ensure collection exists
    try:
        chroma_client.get_collection(CHROMA_COLLECTION_NAME)
    except ValueError:
        chroma_client.create_collection(CHROMA_COLLECTION_NAME)
    
    # Mock the ChromaDB client creation in MemoryManager
    with patch('app.services.memory.chromadb.Client') as mock_client:
        mock_client.return_value = chroma_client
        yield
    
    # Cleanup after test
    if os.path.exists(os.path.join('documents', TEST_DOCUMENT_NAME)):
        os.remove(os.path.join('documents', TEST_DOCUMENT_NAME))
    if os.path.exists(os.path.join('links', TEST_LINK_NAME)):
        os.remove(os.path.join('links', TEST_LINK_NAME))

@pytest.fixture
def mock_embedding():
    """Mock the embedding service to return a test embedding."""
    with patch('app.services.memory.MemoryManager.get_embedding') as mock:
        mock.return_value = TEST_EMBEDDING
        yield mock

@pytest.fixture
def mock_embedding_unavailable():
    """Mock the embedding service to simulate it being unavailable."""
    with patch('app.services.memory.MemoryManager.get_embedding') as mock:
        mock.side_effect = aiohttp.ClientError("Embedding service unavailable")
        yield mock

@pytest.mark.asyncio
async def test_store_memory_with_real_embedding(test_client: TestClient) -> None:
    """Test memory storage using the actual embedding service."""
    # First verify the embedding service is available
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:11434/api/embeddings', 
                                  json={"model": "nomic-embed-text:latest", "prompt": "test"}) as response:
                if response.status != 200:
                    pytest.skip("Embedding service not available")
    except Exception:
        pytest.skip("Embedding service not available")

    test_data = {
        "conversationId": TEST_CONVERSATION_ID,
        "userMessage": {"text": "Test user message with real embedding"},
        "botMessage": {"text": "Test bot response with real embedding"}
    }
    
    response = test_client.post('/store_memory', json=test_data)
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert "memory" in data
    assert data["message"] == "Memory stored successfully"
    
    # Verify memory structure
    memory = data["memory"]
    assert "conversationId" in memory
    assert "userMessage" in memory
    assert "botMessage" in memory
    assert "documents" in memory
    assert "links" in memory
    assert "timestamp" in memory
    
    # Verify specific values
    assert memory["conversationId"] == TEST_CONVERSATION_ID
    assert memory["userMessage"] == "Test user message with real embedding"
    assert memory["botMessage"] == "Test bot response with real embedding"

@pytest.mark.asyncio
async def test_store_memory_success(test_client: TestClient, mock_embedding: MagicMock) -> None:
    """Test successful memory storage with all fields using mocked embedding."""
    test_data = {
        "conversationId": TEST_CONVERSATION_ID,
        "userMessage": {"text": "Test user message"},
        "botMessage": {"text": "Test bot response"},
        "documents": [TEST_DOCUMENT_NAME],
        "links": [TEST_LINK_NAME]
    }
    
    response = test_client.post('/store_memory', json=test_data)
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert "memory" in data
    assert data["message"] == "Memory stored successfully"
    
    # Verify memory structure
    memory = data["memory"]
    assert "conversationId" in memory
    assert "userMessage" in memory
    assert "botMessage" in memory
    assert "documents" in memory
    assert "links" in memory
    assert "timestamp" in memory
    
    # Verify specific values
    assert memory["conversationId"] == TEST_CONVERSATION_ID
    assert memory["userMessage"] == "Test user message"
    assert memory["botMessage"] == "Test bot response"
    assert memory["documents"] == [TEST_DOCUMENT_NAME]
    assert memory["links"] == [TEST_LINK_NAME]
    
    # Verify embedding was called
    mock_embedding.assert_called()

@pytest.mark.asyncio
async def test_store_memory_embedding_unavailable(test_client: TestClient, mock_embedding_unavailable: MagicMock) -> None:
    """Test memory storage when embedding service is unavailable."""
    test_data = {
        "conversationId": TEST_CONVERSATION_ID,
        "userMessage": {"text": "Test message"},
        "botMessage": {"text": "Test response"}
    }
    
    response = test_client.post('/store_memory', json=test_data)
    assert response.status_code == 503  # Service Unavailable
    data = response.json()
    assert "detail" in data
    assert "Embedding service unavailable" in data["detail"]

@pytest.mark.asyncio
async def test_store_memory_minimal_data(test_client: TestClient, mock_embedding: MagicMock) -> None:
    """Test memory storage with minimal required data using mocked embedding."""
    test_data = {
        "conversationId": TEST_CONVERSATION_ID,
        "userMessage": {"text": "Minimal test message"},
        "botMessage": {"text": "Minimal bot response"}
    }
    
    response = test_client.post('/store_memory', json=test_data)
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert "memory" in data
    assert data["message"] == "Memory stored successfully"
    
    # Verify embedding was called
    mock_embedding.assert_called()

@pytest.mark.asyncio
async def test_store_memory_no_messages(test_client: TestClient) -> None:
    """Test memory storage with no messages (should fail)."""
    test_data = {
        "conversationId": TEST_CONVERSATION_ID,
        "documents": [TEST_DOCUMENT_NAME]
    }
    
    response = test_client.post('/store_memory', json=test_data)
    assert response.status_code == 422  # FastAPI validation error
    data = response.json()
    assert "detail" in data

@pytest.mark.asyncio
async def test_store_memory_invalid_document(test_client: TestClient, mock_embedding: MagicMock) -> None:
    """Test memory storage with non-existent document."""
    test_data = {
        "conversationId": TEST_CONVERSATION_ID,
        "userMessage": {"text": "Test message"},
        "botMessage": {"text": "Test response"},
        "documents": ["non_existent_doc.txt"]
    }
    
    response = test_client.post('/store_memory', json=test_data)
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Failed to store memory" in data["detail"]

@pytest.mark.asyncio
async def test_store_memory_invalid_link(test_client: TestClient, mock_embedding: MagicMock) -> None:
    """Test memory storage with non-existent link."""
    test_data = {
        "conversationId": TEST_CONVERSATION_ID,
        "userMessage": {"text": "Test message"},
        "botMessage": {"text": "Test response"},
        "links": ["non_existent_link.json"]
    }
    
    response = test_client.post('/store_memory', json=test_data)
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Failed to store memory" in data["detail"]

@pytest.mark.asyncio
async def test_store_memory_malformed_json(test_client: TestClient) -> None:
    """Test memory storage with malformed JSON."""
    response = test_client.post('/store_memory', data="invalid json")
    assert response.status_code == 422  # FastAPI validation error
    data = response.json()
    assert "detail" in data 