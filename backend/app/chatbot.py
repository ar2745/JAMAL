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
from services.analytics import AnalyticsService
from services.chatbot import Chatbot
from services.memory import MemoryManager
from services.response import ResponseGenerator
from services.swagger_config import SwaggerConfig
from werkzeug.utils import secure_filename

try:
    from services.llm_integration import LLMIntegration, ModelType

    from .image_generation import ImageGenerator
except ImportError:
    from image_generation import ImageGenerator
    from services.llm_integration import LLMIntegration, ModelType

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

# Initialize Swagger
swagger = Swagger(app, config=SwaggerConfig.get_config(), template=SwaggerConfig.get_template())

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

# Initialize services
analytics_service = AnalyticsService()
memory_manager = MemoryManager()
llm_integration = LLMIntegration()
response_generator = ResponseGenerator(llm_integration)
chatbot = Chatbot("http://localhost:11434/api/generate")

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
    metadata = data.get('metadata', {})
    is_reasoning_mode = metadata.get('isReasoningMode', False)
    
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
            if is_reasoning_mode:
                response = asyncio.run(chatbot.get_reasoned_response(user_input))
            else:
                response = asyncio.run(chatbot.get_simple_response(user_input))
        # Handle link-based chat
        elif link and link in chatbot.links:
            if is_reasoning_mode:
                response = asyncio.run(chatbot.get_reasoned_response(user_input))
            else:
                response = asyncio.run(chatbot.get_simple_response(user_input))
        # Handle regular chat
        else:
            if is_reasoning_mode:
                response = asyncio.run(chatbot.get_reasoned_response(user_input))
            else:
                response = asyncio.run(chatbot.get_simple_response(user_input))
        
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
        metadata = chatbot.extract_metadata(url)
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

@app.route('/generate_image', methods=['POST'])
@swag_from({
    "tags": ["Image Generation"],
    "parameters": [
        {
            "name": "prompt",
            "in": "body",
            "schema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "negative_prompt": {"type": "string"},
                    "num_inference_steps": {"type": "integer", "default": 50},
                    "guidance_scale": {"type": "number", "default": 7.5},
                    "width": {"type": "integer", "default": 512},
                    "height": {"type": "integer", "default": 512},
                    "seed": {"type": "integer", "default": None}
                },
                "required": ["prompt"]
            }
        }
    ],
    "responses": {
        "200": {
            "description": "Image generated successfully",
            "schema": {
                "properties": {
                    "image_url": {"type": "string"},
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string"},
                            "negative_prompt": {"type": "string"},
                            "num_inference_steps": {"type": "integer"},
                            "guidance_scale": {"type": "number"},
                            "width": {"type": "integer"},
                            "height": {"type": "integer"},
                            "seed": {"type": "integer"},
                            "generation_time": {"type": "number"}
                        }
                    }
                }
            }
        },
        "400": {"description": "Invalid request parameters"},
        "500": {"description": "Image generation failed"}
    }
})
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
            
        # Get optional parameters with defaults
        negative_prompt = data.get('negative_prompt', "")
        num_inference_steps = data.get('num_inference_steps', 50)
        guidance_scale = data.get('guidance_scale', 7.5)
        width = data.get('width', 512)
        height = data.get('height', 512)
        seed = data.get('seed')
        
        # Generate image using the ImageGenerator
        image_generator = ImageGenerator()
        result = asyncio.run(image_generator.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            width=width,
            height=height,
            seed=seed
        ))
        
        return jsonify({
            "image_url": result["image_url"],
            "metadata": {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "width": width,
                "height": height,
                "seed": seed,
                "generation_time": result["generation_time"]
            }
        })
        
    except Exception as e:
        logger.error(f"Image generation failed: {str(e)}")
        return jsonify({"error": "Image generation failed"}), 500

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(asgi_app, host="0.0.0.0", port=5000)