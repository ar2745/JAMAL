import asyncio
import json
import logging
import os
import re
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import chromadb
import docx
import PyPDF2
import requests
from asgiref.wsgi import WsgiToAsgi
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from flasgger import Swagger, swag_from
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

try:
    from .llm_integration import LLMIntegration, ModelType
except ImportError:
    from llm_integration import LLMIntegration, ModelType

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5174"}})

# Convert Flask app to ASGI
asgi_app = WsgiToAsgi(app)

CHATS_FOLDER = 'chats'
UPLOADS_FOLDER = 'uploads'
LINKS_FOLDER = 'links'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'json', 'docx'}

app.config['CHATS_FOLDER'] = CHATS_FOLDER
app.config['UPLOADS_FOLDER'] = UPLOADS_FOLDER
app.config['LINKS_FOLDER'] = LINKS_FOLDER

if not os.path.exists(CHATS_FOLDER):
    os.makedirs(CHATS_FOLDER)

if not os.path.exists(UPLOADS_FOLDER):
    os.makedirs(UPLOADS_FOLDER)

if not os.path.exists(LINKS_FOLDER):
    os.makedirs(LINKS_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class AnalyticsService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # In-memory storage for analytics data
        self._chat_stats = defaultdict(lambda: {
            'message_count': 0,
            'last_activity': None,
            'document_count': 0,
            'link_count': 0,
            'active_users': set(),
            'message_history': []
        })
        self._document_stats = defaultdict(lambda: {
            'count': 0,
            'total_size': 0,
            'types': defaultdict(int),
            'upload_history': []
        })
        self._link_stats = defaultdict(lambda: {
            'count': 0,
            'domains': defaultdict(int),
            'share_history': []
        })
        self._usage_stats = {
            'daily_active': set(),
            'weekly_active': set(),
            'monthly_active': set(),
            'peak_hours': [0] * 24,
            'concurrent_users': 0,
            'response_times': [],
            'error_rates': defaultdict(int)
        }
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self._cleanup_thread.start()

    def _periodic_cleanup(self):
        """Periodically clean up old data."""
        while True:
            self.cleanup_old_data()
            time.sleep(3600)  # Run cleanup every hour

    def track_chat_activity(self, chat_id: str, message_count: int = 1, user_id: Optional[str] = None):
        """Track chat activity and message count."""
        stats = self._chat_stats[chat_id]
        stats['message_count'] += message_count
        stats['last_activity'] = datetime.now()
        
        if user_id:
            stats['active_users'].add(user_id)
            
        # Track message history
        stats['message_history'].append({
            'timestamp': datetime.now(),
            'user_id': user_id,
            'count': message_count
        })

    def track_document_upload(self, chat_id: str, file_type: str, file_size: int, user_id: Optional[str] = None):
        """Track document upload statistics."""
        chat_stats = self._chat_stats[chat_id]
        doc_stats = self._document_stats[chat_id]
        
        chat_stats['document_count'] += 1
        doc_stats['count'] += 1
        doc_stats['total_size'] += file_size
        doc_stats['types'][file_type] += 1
        
        # Track upload history
        doc_stats['upload_history'].append({
            'timestamp': datetime.now(),
            'user_id': user_id,
            'file_type': file_type,
            'file_size': file_size
        })

    def track_link_share(self, chat_id: str, domain: str, user_id: Optional[str] = None):
        """Track link sharing statistics."""
        chat_stats = self._chat_stats[chat_id]
        link_stats = self._link_stats[chat_id]
        
        chat_stats['link_count'] += 1
        link_stats['count'] += 1
        link_stats['domains'][domain] += 1
        
        # Track share history
        link_stats['share_history'].append({
            'timestamp': datetime.now(),
            'user_id': user_id,
            'domain': domain
        })

    def track_user_activity(self, user_id: str):
        """Track user activity for engagement metrics."""
        now = datetime.now()
        
        # Update daily active users
        self._usage_stats['daily_active'].add(user_id)
        
        # Update weekly active users
        if now.weekday() == 0:  # Monday
            self._usage_stats['weekly_active'].clear()
        self._usage_stats['weekly_active'].add(user_id)
        
        # Update monthly active users
        if now.day == 1:  # First day of month
            self._usage_stats['monthly_active'].clear()
        self._usage_stats['monthly_active'].add(user_id)
        
        # Track peak hours
        hour = now.hour
        self._usage_stats['peak_hours'][hour] += 1
        
        # Update concurrent users
        self._usage_stats['concurrent_users'] = len(self._usage_stats['daily_active'])

    def track_response_time(self, response_time: float):
        """Track response time for performance monitoring."""
        self._usage_stats['response_times'].append({
            'timestamp': datetime.now(),
            'response_time': response_time
        })
        # Keep only last 1000 response times
        if len(self._usage_stats['response_times']) > 1000:
            self._usage_stats['response_times'] = self._usage_stats['response_times'][-1000:]

    def track_error(self, error_type: str):
        """Track error occurrences."""
        self._usage_stats['error_rates'][error_type] += 1

    def get_chat_statistics(self, chat_id: Optional[str] = None) -> Dict:
        """Get chat statistics for a specific chat or all chats."""
        if chat_id:
            stats = dict(self._chat_stats[chat_id])
            # Add real-time metrics
            stats['active_users_count'] = len(stats['active_users'])
            stats['recent_messages'] = [
                msg for msg in stats['message_history']
                if (datetime.now() - msg['timestamp']).total_seconds() < 3600
            ]
            return stats
        
        total_stats = {
            'total_chats': len(self._chat_stats),
            'total_messages': sum(stats['message_count'] for stats in self._chat_stats.values()),
            'total_documents': sum(stats['document_count'] for stats in self._chat_stats.values()),
            'total_links': sum(stats['link_count'] for stats in self._chat_stats.values()),
            'active_chats': sum(1 for stats in self._chat_stats.values() 
                              if stats['last_activity'] and 
                              (datetime.now() - stats['last_activity']).days < 7),
            'total_active_users': len(set().union(*[stats['active_users'] 
                                                  for stats in self._chat_stats.values()]))
        }
        return total_stats

    def get_document_statistics(self, chat_id: Optional[str] = None) -> Dict:
        """Get document statistics for a specific chat or all chats."""
        if chat_id:
            stats = dict(self._document_stats[chat_id])
            # Add real-time metrics
            stats['recent_uploads'] = [
                upload for upload in stats['upload_history']
                if (datetime.now() - upload['timestamp']).total_seconds() < 3600
            ]
            return stats
        
        total_stats = {
            'total_documents': sum(stats['count'] for stats in self._document_stats.values()),
            'total_size': sum(stats['total_size'] for stats in self._document_stats.values()),
            'types': defaultdict(int),
            'recent_uploads': []
        }
        
        for stats in self._document_stats.values():
            for file_type, count in stats['types'].items():
                total_stats['types'][file_type] += count
            # Add recent uploads from all chats
            total_stats['recent_uploads'].extend([
                upload for upload in stats['upload_history']
                if (datetime.now() - upload['timestamp']).total_seconds() < 3600
            ])
                
        return total_stats

    def get_link_statistics(self, chat_id: Optional[str] = None) -> Dict:
        """Get link statistics for a specific chat or all chats."""
        if chat_id:
            stats = dict(self._link_stats[chat_id])
            # Add real-time metrics
            stats['recent_shares'] = [
                share for share in stats['share_history']
                if (datetime.now() - share['timestamp']).total_seconds() < 3600
            ]
            return stats
        
        total_stats = {
            'total_links': sum(stats['count'] for stats in self._link_stats.values()),
            'domains': defaultdict(int),
            'recent_shares': []
        }
        
        for stats in self._link_stats.values():
            for domain, count in stats['domains'].items():
                total_stats['domains'][domain] += count
            # Add recent shares from all chats
            total_stats['recent_shares'].extend([
                share for share in stats['share_history']
                if (datetime.now() - share['timestamp']).total_seconds() < 3600
            ])
                
        return total_stats

    def get_usage_statistics(self) -> Dict:
        """Get usage statistics including active users and peak hours."""
        # Calculate average response time for last hour
        recent_response_times = [
            rt['response_time'] for rt in self._usage_stats['response_times']
            if (datetime.now() - rt['timestamp']).total_seconds() < 3600
        ]
        avg_response_time = sum(recent_response_times) / len(recent_response_times) if recent_response_times else 0
        
        return {
            'daily_active_users': len(self._usage_stats['daily_active']),
            'weekly_active_users': len(self._usage_stats['weekly_active']),
            'monthly_active_users': len(self._usage_stats['monthly_active']),
            'concurrent_users': self._usage_stats['concurrent_users'],
            'peak_hours': self._usage_stats['peak_hours'],
            'average_response_time': avg_response_time,
            'error_rates': dict(self._usage_stats['error_rates'])
        }

    def cleanup_old_data(self, days: int = 30):
        """Clean up data older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clean up chat stats
        for chat_id, stats in list(self._chat_stats.items()):
            if stats['last_activity'] and stats['last_activity'] < cutoff_date:
                del self._chat_stats[chat_id]
                if chat_id in self._document_stats:
                    del self._document_stats[chat_id]
                if chat_id in self._link_stats:
                    del self._link_stats[chat_id]
            else:
                # Clean up message history
                stats['message_history'] = [
                    msg for msg in stats['message_history']
                    if msg['timestamp'] > cutoff_date
                ]
        
        # Clean up document stats
        for stats in self._document_stats.values():
            stats['upload_history'] = [
                upload for upload in stats['upload_history']
                if upload['timestamp'] > cutoff_date
            ]
        
        # Clean up link stats
        for stats in self._link_stats.values():
            stats['share_history'] = [
                share for share in stats['share_history']
                if share['timestamp'] > cutoff_date
            ]
        
        # Clean up usage stats
        if datetime.now().day == 1:  # First day of month
            self._usage_stats['monthly_active'].clear()
        if datetime.now().weekday() == 0:  # Monday
            self._usage_stats['weekly_active'].clear()
        if datetime.now().hour == 0:  # Midnight
            self._usage_stats['daily_active'].clear()
            self._usage_stats['peak_hours'] = [0] * 24
            
        # Clean up response times
        self._usage_stats['response_times'] = [
            rt for rt in self._usage_stats['response_times']
            if rt['timestamp'] > cutoff_date
        ]

# Initialize analytics service
analytics_service = AnalyticsService()

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
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.documents = {}
        self.links = {}
        self.memory_manager = MemoryManager()
        self.response_generator = ResponseGenerator(self)
        self.llm_integration = LLMIntegration(api_url)  # Initialize LLM integration
        self.load_persisted_data()

    def load_persisted_data(self):
        """Load persisted documents and links from disk."""
        try:
            # Load documents
            for filename in os.listdir(UPLOADS_FOLDER):
                if filename.endswith('.meta.json'):
                    continue
                filepath = os.path.join(UPLOADS_FOLDER, filename)
                metadata_path = os.path.join(UPLOADS_FOLDER, f"{filename}.meta.json")
                
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        self.documents[filename] = metadata.get('content', '')
            
            # Load links
            for link_dir in os.listdir(LINKS_FOLDER):
                link_path = os.path.join(LINKS_FOLDER, link_dir)
                if not os.path.isdir(link_path):
                    continue
                    
                metadata_path = os.path.join(link_path, 'meta.json')
                content_path = os.path.join(link_path, 'content.txt')
                
                if os.path.exists(metadata_path) and os.path.exists(content_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    with open(content_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    self.links[link_dir] = {
                        'url': metadata.get('url'),
                        'title': metadata.get('title'),
                        'description': metadata.get('description'),
                        'image': metadata.get('image'),
                        'content': content,
                        'timestamp': metadata.get('timestamp')
                    }
        except Exception as e:
            logger.error(f"Error loading persisted data: {e}")

    def persist_document(self, filename: str, content: str, metadata: dict):
        """Persist document and its metadata to disk."""
        try:
            filepath = os.path.join(UPLOADS_FOLDER, filename)
            metadata_path = os.path.join(UPLOADS_FOLDER, f"{filename}.meta.json")
            
            # Save content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Save metadata
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
        except Exception as e:
            logger.error(f"Error persisting document: {e}")

    def persist_link(self, link_id: str, link_data: dict):
        """Persist link and its metadata to disk."""
        try:
            # Create link directory
            link_dir = os.path.join(LINKS_FOLDER, link_id)
            os.makedirs(link_dir, exist_ok=True)
            
            # Save metadata
            metadata_path = os.path.join(link_dir, 'meta.json')
            with open(metadata_path, 'w') as f:
                json.dump(link_data, f)
            
            # Save content
            content_path = os.path.join(link_dir, 'content.txt')
            with open(content_path, 'w', encoding='utf-8') as f:
                f.write(link_data.get('content', ''))
        except Exception as e:
            logger.error(f"Error persisting link: {e}")

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
        try:
            # Extract metadata
            metadata = extract_metadata(url)
            
            # Create a unique ID for the link
            link_id = secure_filename(f"{url}_{datetime.utcnow().timestamp()}")
            
            # Create link data structure
            link_data = {
                'url': url,
                'title': metadata.get('title'),
                'description': metadata.get('description'),
                'image': metadata.get('image'),
                'content': metadata.get('content'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Persist link data
            self.persist_link(link_id, link_data)
            
            # Store in memory
            self.links[link_id] = link_data
            
            return link_data
        except Exception as e:
            logger.error(f"Error extracting data from web page: {e}")
            raise

def extract_metadata(url):
    try:
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
            
        # Extract image - Try multiple sources
        image = None
        # Try Open Graph image first
        og_image = soup.find('meta', property='og:image')
        if og_image:
            image = og_image.get('content')
        # Try Twitter card image
        if not image:
            twitter_image = soup.find('meta', name='twitter:image')
            if twitter_image:
                image = twitter_image.get('content')
        # Try first image in article
        if not image:
            article_image = soup.find('img')
            if article_image:
                image = article_image.get('src')
        # Try favicon as last resort
        if not image:
            favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
            if favicon:
                image = favicon.get('href')
            
        # Make image URL absolute if it's relative
        if image and not image.startswith(('http://', 'https://')):
            from urllib.parse import urljoin
            image = urljoin(url, image)
            
        return {
            'title': title,
            'description': description,
            'image': image,
            'content': soup.get_text(separator=' ', strip=True)
        }
        
    except requests.exceptions.RequestException as e:
        raise Exception(f'Failed to fetch URL: {str(e)}')
    except Exception as e:
        raise Exception(f'An error occurred: {str(e)}')

# Initialize chatbot with API URL
chatbot = Chatbot("http://localhost:11434/api/generate")

# Swagger configuration
swagger_config = {
    "headers": [],
    "specs": [{
        "endpoint": 'apispec',
        "route": '/apispec.json',
        "rule_filter": lambda rule: True,
        "model_filter": lambda tag: True,
    }],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs"
}

swagger_template = {
    "info": {
        "title": "Responsive Chat API",
        "description": "API documentation for the Responsive Chat application",
        "version": "1.0"
    },
    "schemes": ["http", "https"]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

@app.route('/', methods=['GET'])
@swag_from({
    "tags": ["General"],
    "responses": {
        "200": {
            "description": "Welcome message",
            "schema": {"properties": {"message": {"type": "string"}}}
        }
    }
})
def home():
    return jsonify({"message": "Welcome to the ChatBot API"})

@app.route('/documents', methods=['GET'])
@swag_from({
    "tags": ["Documents"],
    "responses": {
        "200": {
            "description": "List of documents",
            "schema": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }
})
def list_documents():
    documents = []
    for filename, content in chatbot.documents.items():
        metadata_path = os.path.join(app.config['UPLOADS_FOLDER'], f"{filename}.meta.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                documents.append({
                    'id': filename,
                    'filename': filename,
                    'content': content,
                    'type': metadata.get('type', 'text/plain'),
                    'size': metadata.get('size', 0),
                    'timestamp': metadata.get('timestamp')
                })
    return jsonify({"documents": documents})

@app.route('/links', methods=['GET'])
@swag_from({
    "tags": ["Links"],
    "responses": {
        "200": {
            "description": "List of processed links",
            "schema": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }
})
def list_links():
    links = []
    for link_id, link_data in chatbot.links.items():
        link_dir = os.path.join(app.config['LINKS_FOLDER'], link_id)
        metadata_path = os.path.join(link_dir, 'meta.json')
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                links.append({
                    'id': link_id,
                    'url': link_data['url'],
                    'title': link_data.get('title'),
                    'description': link_data.get('description'),
                    'content': link_data.get('content'),
                    'timestamp': link_data.get('timestamp')
                })
    return jsonify({"links": links})

@app.route('/document_upload', methods=['POST'])
@swag_from({
    "tags": ["Documents"],
    "parameters": [
        {
            "name": "file",
            "in": "formData",
            "type": "file",
            "required": True,
            "description": "Document to upload"
        }
    ],
    "responses": {
        "200": {
            "description": "Document uploaded successfully",
            "schema": {"properties": {"message": {"type": "string"}}}
        },
        "400": {"description": "Invalid file"},
        "500": {"description": "Upload failed"}
    }
})
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOADS_FOLDER'], filename)
        file.save(filepath)
        
        try:
            content = chatbot.extract_text_from_file(filepath)
            chatbot.documents[filename] = content
            
            # Create metadata
            metadata = {
                'type': file.content_type,
                'size': os.path.getsize(filepath),
                'timestamp': datetime.utcnow().isoformat(),
                'content': content
            }
            
            # Persist document
            chatbot.persist_document(filename, content, metadata)
            
            # Track document upload in analytics
            chat_id = request.args.get('chat_id', 'default')
            user_id = request.args.get('user_id', 'anonymous')
            analytics_service.track_document_upload(chat_id, file.content_type, metadata['size'], user_id)
            
            response_data = {
                "message": "File uploaded successfully",
                "content": content,
                "metadata": metadata
            }
            return jsonify(response_data), 200
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            analytics_service.track_error("file_upload_error")
            return jsonify({"error": str(e)}), 500
            
    return jsonify({"error": "File type not allowed"}), 400

@app.route('/document_delete', methods=['POST'])
@swag_from({
    "tags": ["Documents"],
    "parameters": [
        {
            "name": "filename",
            "in": "body",
            "schema": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"}
                }
            },
            "required": True,
            "description": "Name of the file to delete"
        }
    ],
    "responses": {
        "200": {
            "description": "Document deleted successfully",
            "schema": {"properties": {"message": {"type": "string"}}}
        },
        "400": {"description": "No filename provided"},
        "404": {"description": "File not found"},
        "500": {"description": "Deletion failed"}
    }
})
def delete_document():
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    uploads_dir = app.config['UPLOADS_FOLDER']
    filepath = os.path.join(uploads_dir, filename)
    metadata_path = os.path.join(uploads_dir, f"{filename}.meta.json")

    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    try:
        # Delete both the file and its metadata
        os.remove(filepath)
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
        return jsonify({"message": "File deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/link_upload', methods=['POST'])
@swag_from({
    "tags": ["Links"],
    "parameters": [
        {
            "name": "url",
            "in": "body",
            "schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                }
            },
            "required": True
        }
    ],
    "responses": {
        "200": {
            "description": "Link processed successfully",
            "schema": {"properties": {"message": {"type": "string"}}}
        },
        "400": {"description": "Invalid URL"},
        "500": {"description": "Processing failed"}
    }
})
def process_link():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        url = data.get('url')
        if not url:
            return jsonify({"error": "No URL provided"}), 400

        # Extract and store link data
        link_data = asyncio.run(chatbot.extract_data_from_web_page(url))
        link_id = link_data['url']  # Use URL as ID
        
        # Track link share in analytics
        chat_id = request.args.get('chat_id', 'default')
        user_id = request.args.get('user_id', 'anonymous')
        domain = url.split('/')[2]  # Extract domain from URL
        analytics_service.track_link_share(chat_id, domain, user_id)
        
        return jsonify({
            "message": "Link processed successfully",
            "link": {
                "id": link_id,
                "title": link_data['title'],
                "description": link_data['description'],
                "image": link_data.get('image'),
                "timestamp": link_data['timestamp']
            }
        }), 200
    except Exception as e:
        logger.error(f"Error processing link: {e}")
        analytics_service.track_error("link_upload_error")
        return jsonify({"error": str(e)}), 500

@app.route('/link_delete', methods=['POST'])
@swag_from({
    "tags": ["Links"],
    "parameters": [
        {
            "name": "filename",
            "in": "body",
            "schema": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"}
                }
            },
            "required": True,
            "description": "Name of the link file to delete"
        }
    ],
    "responses": {
        "200": {
            "description": "Link deleted successfully",
            "schema": {"properties": {"response": {"type": "string"}}}
        },
        "400": {"description": "No filename provided"},
        "404": {"description": "File not found"},
        "500": {"description": "Deletion failed"}
    }
})
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
@swag_from({
    "tags": ["Memory"],
    "parameters": [
        {
            "name": "memory",
            "in": "body",
            "schema": {
                "type": "object",
                "properties": {
                    "userMessage": {"type": "string"},
                    "botMessage": {"type": "string"},
                    "documents": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "links": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "conversationId": {"type": "string"}
                }
            },
            "required": True
        }
    ],
    "responses": {
        "200": {
            "description": "Memory stored successfully",
            "schema": {
                "properties": {
                    "message": {"type": "string"},
                    "memory": {"type": "object"}
                }
            }
        },
        "400": {"description": "No message provided"},
        "500": {"description": "Storage failed"}
    }
})
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
@swag_from({
    "tags": ["Memory"],
    "parameters": [
        {
            "name": "query",
            "in": "body",
            "schema": {
                "type": "object",
                "properties": {
                    "conversationId": {"type": "string"},
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 5}
                }
            },
            "required": True
        }
    ],
    "responses": {
        "200": {
            "description": "Retrieved memories",
            "schema": {
                "properties": {
                    "memories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "timestamp": {"type": "string"},
                                "type": {"type": "string"}
                            }
                        }
                    }
                }
            }
        },
        "400": {"description": "No conversation ID provided"},
        "500": {"description": "Retrieval failed"}
    }
})
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
@swag_from({
    "tags": ["Chat"],
    "parameters": [
        {
            "name": "message",
            "in": "body",
            "type": "object",
            "required": True,
            "properties": {
                "message": {"type": "string"},
                "type": {"type": "string"},
                "metadata": {"type": "object"},
                "conversation_id": {"type": "string"},
                "document": {"type": "string"},
                "link": {"type": "string"},
                "user_id": {"type": "string"},
                "context": {"type": "string"}
            }
        }
    ],
    "responses": {
        "200": {
            "description": "Successful response",
            "schema": {"properties": {"response": {"type": "string"}}}
        },
        "400": {"description": "Bad request"},
        "500": {"description": "Internal server error"}
    }
})
def chat():
    start_time = datetime.now()
    data = request.get_json()
    user_input = data.get('message')
    conversation_id = data.get('conversation_id')
    document_name = data.get('document')
    link = data.get('link')
    user_id = data.get('user_id', 'anonymous')
    
    # Track user activity
    analytics_service.track_user_activity(user_id)
    
    if not user_input:
        return jsonify({'response': 'Error: Empty input'}), 400
    elif len(user_input) > 512:
        return jsonify({'response': 'Error: Input too long'}), 400
    elif not isinstance(user_input, str):
        return jsonify({'response': 'Error: Invalid input type'}), 400
    
    # Track chat activity
    chat_id = conversation_id or 'default'
    analytics_service.track_chat_activity(chat_id, user_id=user_id)
    
    try:
        # Handle document-based chat
        if document_name and document_name in chatbot.documents:
            response = asyncio.run(chatbot.response_generator.generate_document_response(
                user_input,
                chatbot.documents[document_name]
            ))
        # Handle link-based chat
        elif link and link in chatbot.links:
            response = asyncio.run(chatbot.response_generator.generate_link_response(
                user_input,
                chatbot.links[link]['content']
            ))
        # Handle regular chat
        else:
            response = asyncio.run(chatbot.response_generator.generate_simple_response(user_input))
        
        # Store the conversation in memory
        if conversation_id:
            asyncio.run(chatbot.memory_manager.store_memory(
                conversation_id,
                user_input,
                response,
                [document_name] if document_name else None,
                [link] if link else None
            ))
        
        # Track response time
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        analytics_service.track_response_time(response_time)
        
        return jsonify({'response': response})
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        analytics_service.track_error("chat_error")
        return jsonify({'error': str(e)}), 500

@app.route('/api/link_metadata', methods=['POST'])
@swag_from({
    "tags": ["Links"],
    "parameters": [
        {
            "name": "url",
            "in": "body",
            "schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                }
            },
            "required": True
        }
    ],
    "responses": {
        "200": {
            "description": "Link metadata retrieved successfully",
            "schema": {
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "image": {"type": "string"},
                    "content": {"type": "string"}
                }
            }
        },
        "400": {"description": "URL is required"},
        "500": {"description": "Metadata extraction failed"}
    }
})
def get_link_metadata():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        metadata = extract_metadata(url)
        return jsonify(metadata)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add analytics endpoints
@app.route('/analytics/chat', methods=['GET'])
@swag_from({
    "tags": ["Analytics"],
    "parameters": [
        {
            "name": "chat_id",
            "in": "query",
            "type": "string",
            "required": False
        }
    ],
    "responses": {
        "200": {
            "description": "Chat analytics data",
            "schema": {
                "type": "object",
                "properties": {
                    "message_count": {"type": "integer"},
                    "last_activity": {"type": "string"},
                    "document_count": {"type": "integer"},
                    "link_count": {"type": "integer"}
                }
            }
        }
    }
})
def get_chat_analytics():
    chat_id = request.args.get('chat_id')
    stats = analytics_service.get_chat_statistics(chat_id)
    return jsonify(stats)

@app.route('/analytics/documents', methods=['GET'])
@swag_from({
    "tags": ["Analytics"],
    "parameters": [
        {
            "name": "chat_id",
            "in": "query",
            "type": "string",
            "required": False
        }
    ],
    "responses": {
        "200": {
            "description": "Document analytics data",
            "schema": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer"},
                    "total_size": {"type": "integer"},
                    "types": {"type": "object"}
                }
            }
        }
    }
})
def get_document_analytics():
    chat_id = request.args.get('chat_id')
    stats = analytics_service.get_document_statistics(chat_id)
    return jsonify(stats)

@app.route('/analytics/links', methods=['GET'])
@swag_from({
    "tags": ["Analytics"],
    "parameters": [
        {
            "name": "chat_id",
            "in": "query",
            "type": "string",
            "required": False
        }
    ],
    "responses": {
        "200": {
            "description": "Link analytics data",
            "schema": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer"},
                    "domains": {"type": "object"}
                }
            }
        }
    }
})
def get_link_analytics():
    chat_id = request.args.get('chat_id')
    stats = analytics_service.get_link_statistics(chat_id)
    return jsonify(stats)

@app.route('/analytics/usage', methods=['GET'])
@swag_from({
    "tags": ["Analytics"],
    "responses": {
        "200": {
            "description": "Usage analytics data",
            "schema": {
                "type": "object",
                "properties": {
                    "daily_active": {"type": "integer"},
                    "weekly_active": {"type": "integer"},
                    "monthly_active": {"type": "integer"},
                    "peak_hours": {
                        "type": "array",
                        "items": {"type": "integer"}
                    }
                }
            }
        }
    }
})
def get_usage_analytics():
    stats = analytics_service.get_usage_statistics()
    return jsonify(stats)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(asgi_app, host="0.0.0.0", port=5000)