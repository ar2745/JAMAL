import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict

import aiohttp
import chromadb
import pytest

from ..app.main import asgi_app, chatbot

# Test configuration
TEST_API_URL = "http://localhost:11434"  # Base URL for Ollama
TEST_CONVERSATION_ID = "test_conversation_123"
TEST_DOCUMENT_NAME = "test_document.txt"
TEST_LINK_NAME = "test_link.json"

@pytest.fixture(autouse=True)
def setup_and_cleanup():
    # Setup: Create necessary directories
    os.makedirs('documents', exist_ok=True)
    os.makedirs('links', exist_ok=True)
    
    # Cleanup: Delete test files after each test
    yield
    
    # Cleanup after test
    if os.path.exists(os.path.join('documents', TEST_DOCUMENT_NAME)):
        os.remove(os.path.join('documents', TEST_DOCUMENT_NAME))
    if os.path.exists(os.path.join('links', TEST_LINK_NAME)):
        os.remove(os.path.join('links', TEST_LINK_NAME))
    
    # Cleanup ChromaDB collection
    try:
        client = chromadb.Client()
        client.delete_collection("chat_memories")
    except Exception as e:
        print(f"Error cleaning up ChromaDB: {e}")

@pytest.fixture
async def test_client():
    async with aiohttp.ClientSession() as session:
        yield session

@pytest.mark.asyncio
async def test_basic_chat(test_client):
    async with test_client.post('http://localhost:5000/chat', json={
        'message': 'Hello, how are you?',
        'conversationId': TEST_CONVERSATION_ID
    }) as response:
        assert response.status == 200
        data = await response.json()
        assert 'response' in data

@pytest.mark.asyncio
async def test_chat_with_reasoning(test_client):
    async with test_client.post('http://localhost:5000/chat', json={
        'message': 'Why is the sky blue?',
        'reasoning': True,
        'conversationId': TEST_CONVERSATION_ID
    }) as response:
        assert response.status == 200
        data = await response.json()
        assert 'response' in data

@pytest.mark.asyncio
async def test_chat_with_document(test_client):
    # First upload a test document
    test_content = "This is a test document content."
    with open(os.path.join('documents', TEST_DOCUMENT_NAME), 'w') as f:
        f.write(test_content)
    
    async with test_client.post('http://localhost:5000/chat', json={
        'message': 'What does the document say?',
        'document': TEST_DOCUMENT_NAME,
        'conversationId': TEST_CONVERSATION_ID
    }) as response:
        assert response.status == 200
        data = await response.json()
        assert 'response' in data

@pytest.mark.asyncio
async def test_chat_with_link(test_client):
    # First create a test link
    test_link_content = {"content": "This is a test link content."}
    with open(os.path.join('links', TEST_LINK_NAME), 'w') as f:
        json.dump(test_link_content, f)
    
    async with test_client.post('http://localhost:5000/chat', json={
        'message': 'What does the link contain?',
        'link': TEST_LINK_NAME,
        'conversationId': TEST_CONVERSATION_ID
    }) as response:
        assert response.status == 200
        data = await response.json()
        assert 'response' in data

# @pytest.mark.asyncio
# async def test_memory_storage_and_retrieval(test_client):
#     # Test storing memory
#     async with test_client.post('http://localhost:5000/store_memory', json={
#         'conversationId': TEST_CONVERSATION_ID,
#         'userMessage': {'text': 'Test user message'},
#         'botMessage': {'text': 'Test bot response'}
#     }) as response:
#         assert response.status == 200
#         data = await response.json()
#         assert 'message' in data
#         assert 'memory' in data

#     # Test retrieving memory
#     async with test_client.post('http://localhost:5000/retrieve_memory', json={
#         'conversationId': TEST_CONVERSATION_ID,
#         'query': 'Test query',
#         'limit': 5
#     }) as response:
#         assert response.status == 200
#         data = await response.json()
#         assert 'memories' in data
#         assert len(data['memories']) > 0
#         # Verify memory structure
#         memory = data['memories'][0]
#         assert 'text' in memory
#         assert 'timestamp' in memory
#         assert 'type' in memory

# @pytest.mark.asyncio
# async def test_chat_with_memory_context(test_client):
#     # First store some memories
#     async with test_client.post('http://localhost:5000/store_memory', json={
#         'conversationId': TEST_CONVERSATION_ID,
#         'userMessage': {'text': 'Previous question'},
#         'botMessage': {'text': 'Previous answer'}
#     }) as response:
#         assert response.status == 200

#     # Then test chat with memory context
#     async with test_client.post('http://localhost:5000/chat', json={
#         'message': 'Follow-up question',
#         'conversationId': TEST_CONVERSATION_ID
#     }) as response:
#         assert response.status == 200
#         data = await response.json()
#         assert 'response' in data

# @pytest.mark.asyncio
# async def test_error_handling(test_client):
#     # Test empty message
#     async with test_client.post('http://localhost:5000/chat', json={
#         'message': '',
#         'conversationId': TEST_CONVERSATION_ID
#     }) as response:
#         assert response.status == 200
#         data = await response.json()
#         assert 'Error: Empty input' in data['response']

#     # Test non-existent document
#     async with test_client.post('http://localhost:5000/chat', json={
#         'message': 'Test message',
#         'document': 'non_existent_doc.txt',
#         'conversationId': TEST_CONVERSATION_ID
#     }) as response:
#         assert response.status == 200
#         data = await response.json()
#         assert 'Error: Document not found' in data['response']

@pytest.mark.asyncio
async def test_goodbye_command(test_client):
    async with test_client.post('http://localhost:5000/chat', json={
        'message': '/bye',
        'conversationId': TEST_CONVERSATION_ID
    }) as response:
        assert response.status == 200
        data = await response.json()
        assert 'response' in data

if __name__ == "__main__":
    pytest.main([__file__]) 