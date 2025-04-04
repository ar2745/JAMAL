import asyncio
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List

import aiohttp
import chromadb
import docx
import PyPDF2
import requests
from asgiref.wsgi import WsgiToAsgi
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

try:
    from .llm_integration import LLMIntegration, ModelType
except ImportError:
    from llm_integration import LLMIntegration, ModelType

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5174"}})

# Convert Flask app to ASGI
asgi_app = WsgiToAsgi(app)

CHATS_FOLDER = 'chats'
DOCUMENTS_FOLDER = 'documents'
LINKS_FOLDER = 'links'
UPLOADS_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'json', 'docx'}

app.config['CHATS_FOLDER'] = CHATS_FOLDER
app.config['DOCUMENTS_FOLDER'] = DOCUMENTS_FOLDER
app.config['LINKS_FOLDER'] = LINKS_FOLDER
app.config['UPLOADS_FOLDER'] = UPLOADS_FOLDER

if not os.path.exists(CHATS_FOLDER):
    os.makedirs(CHATS_FOLDER)

if not os.path.exists(DOCUMENTS_FOLDER):
    os.makedirs(DOCUMENTS_FOLDER)

if not os.path.exists(LINKS_FOLDER):
    os.makedirs(LINKS_FOLDER)

if not os.path.exists(UPLOADS_FOLDER):
    os.makedirs(UPLOADS_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class MemoryManager:
    def __init__(self, api_url: str = "http://localhost:11434"):
        # Remove /api/generate from the URL if it's present
        self.api_url = api_url.replace("/api/generate", "")
        self.embedding_model = "llama2"
        self.fallback_model = "llama2:7b"  # Smaller model as fallback
        try:
            self.client = chromadb.Client()
            # Try to get existing collection or create new one
            try:
                self.collection = self.client.get_collection("chat_memories")
            except ValueError:
                self.collection = self.client.create_collection(
                    name="chat_memories",
                    metadata={"hnsw:space": "cosine"}
                )
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            raise

    async def get_embedding(self, text: str) -> List[float]:
        try:
            # First try with the main model
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_url}/api/embed",
                        json={
                            "model": self.embedding_model,
                            "input": text
                        }
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get("embedding", [])
                        elif response.status == 500 and "memory" in str(await response.text()).lower():
                            # If memory error, try fallback model
                            print("Memory error, trying fallback model...")
                            async with session.post(
                                f"{self.api_url}/api/embed",
                                json={
                                    "model": self.fallback_model,
                                    "input": text
                                }
                            ) as fallback_response:
                                if fallback_response.status == 200:
                                    result = await fallback_response.json()
                                    return result.get("embedding", [])
                        raise Exception(f"Failed to get embedding: {response.status}")
            except Exception as e:
                print(f"Error with main model: {e}")
                # Try fallback model
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_url}/api/embed",
                        json={
                            "model": self.fallback_model,
                            "input": text
                        }
                    ) as fallback_response:
                        if fallback_response.status == 200:
                            result = await fallback_response.json()
                            return result.get("embedding", [])
                        raise Exception(f"Failed to get embedding with fallback: {fallback_response.status}")
        except Exception as e:
            print(f"Error getting embedding: {e}")
            raise

    async def store_memory(self, conversation_id: str, user_message: str, bot_message: str, 
                          documents: List[str] = None, links: List[str] = None) -> Dict[str, Any]:
        try:
            # Create memory entry
            memory_entry = {
                "userMessage": user_message,
                "botMessage": bot_message,
                "documents": documents or [],
                "links": links or [],
                "timestamp": datetime.utcnow().isoformat(),
                "conversationId": conversation_id
            }

            # Generate embeddings for all text content
            texts_to_embed = [user_message, bot_message]
            if documents:
                texts_to_embed.extend(documents)
            if links:
                texts_to_embed.extend(links)

            # Store each piece of text with its embedding in ChromaDB
            for i, text in enumerate(texts_to_embed):
                try:
                    embedding = await self.get_embedding(text)
                    self.collection.add(
                        embeddings=[embedding],
                        documents=[text],
                        metadatas=[{
                            "conversation_id": conversation_id,
                            "timestamp": memory_entry["timestamp"],
                            "type": "user_message" if i == 0 else "bot_message" if i == 1 else "document" if i < len(documents) + 2 else "link"
                        }],
                        ids=[f"{conversation_id}_{i}_{datetime.utcnow().timestamp()}"]
                    )
                except Exception as e:
                    print(f"Error storing memory {i}: {e}")
                    raise

            return memory_entry
        except Exception as e:
            print(f"Error in store_memory: {e}")
            raise

    async def retrieve_relevant_memories(self, conversation_id: str, query: str, 
                                       limit: int = 5) -> List[Dict[str, Any]]:
        try:
            # Get query embedding
            query_embedding = await self.get_embedding(query)

            # Query ChromaDB for similar memories
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where={"conversation_id": conversation_id}
            )

            # Format results into memory entries
            memories = []
            for i in range(len(results['documents'][0])):
                memory = {
                    "text": results['documents'][0][i],
                    "timestamp": results['metadatas'][0][i]["timestamp"],
                    "type": results['metadatas'][0][i]["type"]
                }
                memories.append(memory)

            return memories
        except Exception as e:
            print(f"Error in retrieve_relevant_memories: {e}")
            raise

class ResponseGenerator:
    def __init__(self, chatbot):
        self.chatbot = chatbot

    async def generate_simple_response(self, input_text):
        return await self.chatbot.get_simple_response(input_text)

    async def generate_reasoned_response(self, input_text):
        return await self.chatbot.get_reasoned_response(input_text)

    async def generate_document_response(self, input_text, doc_content):
        combined_input = f"{input_text}\n\nDocument Content:\n{doc_content}"
        return await self.generate_simple_response(combined_input)

    async def generate_link_response(self, input_text, link_content):
        combined_input = f"{input_text}\n\nLink Content:\n{link_content}"
        return await self.generate_simple_response(combined_input)

    async def generate_combined_response(self, input_text, doc_content, link_content):
        combined_input = f"{input_text}\n\nDocument Content:\n{doc_content}\n\nLink Content:\n{link_content}"
        return await self.generate_simple_response(combined_input)

class Chatbot:
    def __init__(self, api_url):
        self.llm_integration = LLMIntegration(api_url)
        self.documents = {}
        self.links = {}
        self.response_generator = ResponseGenerator(self)
        self.memory_manager = MemoryManager(api_url)

    def preprocess_input(self, user_input):
        return user_input.strip().lower()

    async def get_reasoned_response(self, user_input):
        processed_input = self.preprocess_input(user_input)
        reasoned_response = await self.llm_integration.generate_response(processed_input, model_type=ModelType.REASONED)
        return reasoned_response

    async def get_simple_response(self, user_input):
        processed_input = self.preprocess_input(user_input)
        simple_response = await self.llm_integration.generate_response(processed_input, model_type=ModelType.SIMPLE)
        return simple_response

    def extract_text_from_file(self, filepath):
        ext = filepath.rsplit('.', 1)[1].lower()
        if ext == 'pdf':
            return self.extract_text_from_pdf(filepath)
        elif ext == 'txt':
            return self.extract_text_from_txt(filepath)
        elif ext == 'json':
            return self.extract_text_from_json(filepath)
        elif ext == 'docx':
            return self.extract_text_from_docx(filepath)
        return ""

    def extract_text_from_pdf(self, filepath):
        text = ""
        try:
            with open(filepath, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    text += reader.pages[page_num].extract_text()
            return text
        except FileNotFoundError:
            return "Error file not found"
        except Exception as e:
            return f"Error: {e}"

    def extract_text_from_txt(self, filepath):
        try:
            with open(filepath, 'r') as file:
                return file.read()
        except FileNotFoundError:
            return "Error file not found"
        except Exception as e:
            return f"Error: {e}"

    def extract_text_from_json(self, filepath):
        try:
            with open(filepath, 'r') as file:
                data = json.load(file)
                return json.dumps(data, indent=4)
        except FileNotFoundError:
            return "Error file not found"
        except Exception as e:
            return f"Error: {e}"

    def extract_text_from_docx(self, filepath):
        try:
            doc = docx.Document(filepath)
            return "\n".join([para.text for para in doc.paragraphs])
        except FileNotFoundError:
            return "Error file not found"
        except Exception as e:
            return f"Error: {e}"

    async def extract_data_from_web_page(self, url):
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            return result.markdown

chatbot = Chatbot("http://localhost:11434/api/generate")

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the ChatBot API"})

@app.route('/documents', methods=['GET'])
def list_documents():
    return jsonify({"documents": list(chatbot.documents.keys())})

@app.route('/links', methods=['GET'])
def list_links():
    return jsonify({"links": list(chatbot.links.keys())})

@app.route('/document_upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Ensure the upload folder exists
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Check if chatbot object is available and functioning
            try:
                extracted_text = chatbot.extract_text_from_file(filepath)
                chatbot.documents[filename] = extracted_text
                return jsonify({
                    "message": "File uploaded successfully",
                    "filename": filename,
                    "content": extracted_text
                }), 200
            except Exception as e:
                print("Error extracting text:", e)
                return jsonify({"error": f"Error extracting text: {str(e)}"}), 500
        return jsonify({"error": "File type not allowed"}), 400
    except Exception as e:
        print(f"Error during file upload: {e}")
        return jsonify({"error": f"Error during file upload: {str(e)}"}), 500

@app.route('/document_delete', methods=['POST'])
def delete_document():
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({"response": "Error: No filename provided"}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({"response": "Error: File not found"}), 404

    try:
        os.remove(filepath)
        del chatbot.documents[filename]
        return jsonify({"response": "File deleted successfully"}), 200
    except Exception as e:
        return jsonify({"response": f"Error: {e}"}), 500

@app.route('/link_upload', methods=['POST'])
async def crawl():
    data = request.get_json()
    urls = data.get('urls')
    if not urls:
        return jsonify({"response": "Error: Empty input"}), 400

    try:
        response = await chatbot.extract_data_from_web_page(urls)
        if response:
            filename = secure_filename(f"{urls}.json")
            filepath = os.path.join(app.config['LINKS_FOLDER'], filename)
            with open(filepath, 'w') as file:
                json.dump(response, file)
            chatbot.links[filename] = response
            return jsonify({"response": response}), 200
        else:
            return jsonify({"response": "Error: Unable to extract data"}), 500
    except Exception as e:
        return jsonify({"response": f"Error: {e}"}), 500

@app.route('/link_delete', methods=['POST'])
def delete_link():
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({"response": "Error: No filename provided"}), 400

    filepath = os.path.join(app.config['LINKS_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({"response": "Error: File not found"}), 404

    try:
        os.remove(filepath)
        del chatbot.links[filename]
        return jsonify({"response": "File deleted successfully"}), 200
    except Exception as e:
        return jsonify({"response": f"Error: {e}"}), 500

@app.route('/store_memory', methods=['POST'])
async def store_memory():
    data = request.get_json()
    user_message = data.get('userMessage')
    bot_message = data.get('botMessage')
    documents = data.get('documents', [])
    links = data.get('links', [])
    conversation_id = data.get('conversationId')

    if not user_message and not bot_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        memory_entry = await chatbot.memory_manager.store_memory(
            conversation_id,
            user_message.get('text', ''),
            bot_message.get('text', ''),
            documents,
            links
        )
        return jsonify({"message": "Memory stored successfully", "memory": memory_entry}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to store memory: {str(e)}"}), 500

@app.route('/retrieve_memory', methods=['POST'])
async def retrieve_memory():
    data = request.get_json()
    conversation_id = data.get('conversationId')
    query = data.get('query', '')
    limit = data.get('limit', 5)

    if not conversation_id:
        return jsonify({"error": "No conversation ID provided"}), 400

    try:
        memories = await chatbot.memory_manager.retrieve_relevant_memories(
            conversation_id,
            query,
            limit
        )
        return jsonify({"memories": memories}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve memories: {str(e)}"}), 500

@app.route('/chat', methods=['POST'])
async def chat():
    try:
        data = request.get_json()
        message = data.get('message')
        context = data.get('context')
        message_type = data.get('type', 'text')
        metadata = data.get('metadata', {})

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Prepare the prompt with context if available
        prompt = message
        if context:
            prompt = f"""Context from selected sources:
{context}

User question: {message}

Please provide a response based on the context above. If the context is not relevant to the question, you can provide a general response."""

        # Handle file messages
        if message_type == 'file':
            content = metadata.get('content', '')
            if not content:
                return jsonify({'error': 'No file content provided'}), 400

            # Create a prompt for analyzing the file
            prompt = f"""Please analyze this document and provide a brief summary:

Document Name: {metadata.get('fileName', 'Unknown')}
Content:
{content[:2000]}  # Limit content length for the prompt

Please provide:
1. A brief summary of the document
2. Key points or main topics
3. Any notable information or insights

Keep your response concise and focused on the actual content of the document."""
            
            # Get response from LLM
            response = await chatbot.get_simple_response(prompt)
            return jsonify({'response': response})

        # Handle link messages
        elif message_type == 'link':
            url = metadata.get('url')
            if not url:
                return jsonify({'error': 'URL is required for link messages'}), 400

            # Fetch and process the link content
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Extract text content
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Create a prompt that includes the link content
            prompt = f"""I found this link: {url}
Title: {metadata.get('title', 'No title available')}
Description: {metadata.get('description', 'No description available')}

Content from the page:
{text_content[:2000]}  # Limit content length

Please analyze this content and provide a summary or insights."""
            
            # Get response from LLM
            response = await chatbot.get_simple_response(prompt)
            return jsonify({'response': response})

        # Handle regular text messages
        response = await chatbot.get_simple_response(prompt)
        return jsonify({'response': response})

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/link_metadata', methods=['POST'])
def get_link_metadata():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
            
        # Fetch the webpage content
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = None
        og_title = soup.find('meta', property='og:title')
        if og_title:
            title = og_title.get('content')
        if not title:
            title = soup.find('title')
            title = title.text if title else None
        if not title:
            title = url
            
        # Extract description
        description = None
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            description = og_desc.get('content')
        if not description:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content') if meta_desc else None
            
        # Extract image
        image = None
        og_image = soup.find('meta', property='og:image')
        if og_image:
            image = og_image.get('content')
        if not image:
            twitter_image = soup.find('meta', name='twitter:image')
            image = twitter_image.get('content') if twitter_image else None
        if not image:
            favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
            image = favicon.get('href') if favicon else None
            
        # Make image URL absolute if it's relative
        if image and not image.startswith(('http://', 'https://')):
            from urllib.parse import urljoin
            image = urljoin(url, image)
        
        return jsonify({
            'title': title,
            'description': description,
            'image': image
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to fetch URL: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(asgi_app, host="0.0.0.0", port=5000)