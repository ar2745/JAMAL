import asyncio
import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import aiohttp
from fastapi import Body, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, RedirectResponse
from image_generation import ImageGenerator
from pydantic import BaseModel, Field
from services.analytics import AnalyticsService
from services.chatbot import Chatbot
from services.llm_integration import LLMIntegration, ModelType
from services.memory import MemoryManager
from services.response import ResponseGenerator
from services.swagger_config import SwaggerConfig

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CHATS_FOLDER = 'chats'
UPLOADS_FOLDER = 'uploads'
LINKS_FOLDER = 'links'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'json', 'docx'}

# Create necessary directories
for folder in [CHATS_FOLDER, UPLOADS_FOLDER, LINKS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Initialize FastAPI app with proper documentation settings
app = FastAPI(
    title="JAMAL API",
    description="Chatbot API with memory and document processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

################################################## Services ##################################################
# Initialize services
analytics_service = AnalyticsService()
memory_manager = MemoryManager()
llm_integration = LLMIntegration()
response_generator = ResponseGenerator(llm_integration)
chatbot = Chatbot("http://localhost:11434/api/generate")

################################################## Configuration ##################################################
CHATS_FOLDER = 'chats'
UPLOADS_FOLDER = 'uploads'
LINKS_FOLDER = 'links'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'json', 'docx'}

# Load persisted data
def load_persisted_data():
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
                    chatbot.documents[filename] = metadata.get('content', '')
        
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
                    
                chatbot.links[link_dir] = {
                    'url': metadata.get('url'),
                    'title': metadata.get('title'),
                    'description': metadata.get('description'),
                    'image': metadata.get('image'),
                    'content': content,
                    'timestamp': metadata.get('timestamp')
                }
    except Exception as e:
        logger.error(f"Error loading persisted data: {e}")

# Load persisted data on startup
load_persisted_data()

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

################################################## Pydantic Models ##################################################
class Message(BaseModel):
    text: str

class MemoryRequest(BaseModel):
    conversationId: str
    userMessage: Message
    botMessage: Message
    documents: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)

class ChatRequest(BaseModel):
    message: str
    type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    document: Optional[str] = None
    link: Optional[str] = None
    user_id: Optional[str] = None
    context: Optional[str] = None

class LinkRequest(BaseModel):
    url: str

class ImageRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    num_inference_steps: Optional[int] = 50
    guidance_scale: Optional[float] = 7.5
    width: Optional[int] = 512
    height: Optional[int] = 512
    seed: Optional[int] = None

class DocumentResponse(BaseModel):
    id: str
    filename: str
    content: str
    type: str
    size: int
    timestamp: str

class LinkResponse(BaseModel):
    id: str
    url: str
    title: Optional[str]
    description: Optional[str]
    content: Optional[str]
    timestamp: Optional[str]

class MemoryResponse(BaseModel):
    message: str
    memory: Dict[str, Any]

class ChatResponse(BaseModel):
    response: str

class ImageResponse(BaseModel):
    image_url: str
    metadata: Dict[str, Any]

class MemoryEntry(BaseModel):
    id: str
    conversation_id: str
    type: str
    timestamp: str
    text: str

class MemoryViewerResponse(BaseModel):
    entries: List[MemoryEntry]
    total: int
    page: int
    page_size: int

################################################## Chat Routes ##################################################
@app.get("/", response_model=Dict[str, str])
async def home():
    return {"message": "Welcome to the ChatBot API"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = datetime.now()
    
    if not request.message:
        raise HTTPException(status_code=400, detail="Empty input")
    elif len(request.message) > 512:
        raise HTTPException(status_code=400, detail="Input too long")
    
    try:
        # Track user activity
        analytics_service.track_user_activity(request.user_id or 'anonymous')
        
        # Track chat activity
        chat_id = request.conversation_id or 'default'
        analytics_service.track_chat_activity(chat_id, user_id=request.user_id)
        
        # Handle different chat types
        if request.document and request.document in chatbot.documents:
            response = await chatbot.get_reasoned_response(request.message) if request.metadata.get('isReasoningMode') else await chatbot.get_simple_response(request.message)
        elif request.link and request.link in chatbot.links:
            response = await chatbot.get_reasoned_response(request.message) if request.metadata.get('isReasoningMode') else await chatbot.get_simple_response(request.message)
        else:
            response = await chatbot.get_reasoned_response(request.message) if request.metadata.get('isReasoningMode') else await chatbot.get_simple_response(request.message)
        
        # Store in memory if conversation_id exists
        if request.conversation_id:
            await memory_manager.store_memory(
                request.conversation_id,
                request.message,
                response,
                [request.document] if request.document else None,
                [request.link] if request.link else None
            )
        
        # Track response time
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        analytics_service.track_response_time(response_time)
        
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        analytics_service.track_error("chat_error")
        raise HTTPException(status_code=500, detail=str(e))

################################################## Document Routes ##################################################
@app.get("/documents", response_model=Dict[str, List[DocumentResponse]])
async def list_documents():
    documents = []
    for filename, content in chatbot.documents.items():
        metadata_path = os.path.join(UPLOADS_FOLDER, f"{filename}.meta.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                documents.append(DocumentResponse(
                    id=filename,
                    filename=filename,
                    content=content,
                    type=metadata.get('type', 'text/plain'),
                    size=metadata.get('size', 0),
                    timestamp=metadata.get('timestamp')
                ))
    return {"documents": documents}

@app.post("/document_upload", response_model=Dict[str, Any])
async def upload_file(file: UploadFile = File(...)):
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    try:
        content = await file.read()
        filepath = os.path.join(UPLOADS_FOLDER, file.filename)
        
        with open(filepath, 'wb') as f:
            f.write(content)
        
        content_text = chatbot.extract_text_from_file(filepath)
        chatbot.documents[file.filename] = content_text
        analytics_service.track_document_upload(file.filename, file.content_type, os.path.getsize(filepath))
        
        metadata = {
            'type': file.content_type,
            'size': os.path.getsize(filepath),
            'timestamp': datetime.utcnow().isoformat(),
            'content': content_text
        }
        
        chatbot.persist_document(file.filename, content_text, metadata)
        
        return {
            "message": "File uploaded successfully",
            "content": content_text,
            "metadata": metadata
        }
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/document_delete", response_model=Dict[str, str])
async def delete_document(filename: str = Body(...)):
    if not filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    filepath = os.path.join(UPLOADS_FOLDER, filename)
    metadata_path = os.path.join(UPLOADS_FOLDER, f"{filename}.meta.json")
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # Remove from memory
        if filename in chatbot.documents:
            del chatbot.documents[filename]
        
        # Remove from disk
        if os.path.exists(filepath):
            os.remove(filepath)
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
        
        return {"response": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

################################################## Memory Routes ##################################################
@app.post("/store_memory", response_model=Dict[str, Any])
async def store_memory(request: MemoryRequest) -> Dict[str, Any]:
    """Store a memory in the memory system."""
    try:
        memory = await memory_manager.store_memory(
            conversation_id=request.conversationId,
            user_message=request.userMessage.text,
            bot_message=request.botMessage.text,
            documents=request.documents,
            links=request.links
        )
        return {
            "message": "Memory stored successfully",
            "memory": memory
        }
    except aiohttp.ClientError as e:
        logger.error(f"Error storing memory: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Embedding service unavailable"
        )
    except Exception as e:
        logger.error(f"Error storing memory: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store memory: {str(e)}"
        )

@app.get("/memory_viewer", response_model=MemoryViewerResponse)
async def get_memory_entries(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    conversation_id: Optional[str] = None,
    type: Optional[str] = None
) -> MemoryViewerResponse:
    """Retrieve memory entries with pagination and filtering."""
    try:
        # Get all entries from ChromaDB
        collection = memory_manager.collection
        results = collection.get()
        
        # Filter entries
        filtered_entries = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            if conversation_id and metadata['conversation_id'] != conversation_id:
                continue
            if type and metadata['type'] != type:
                continue
                
            filtered_entries.append({
                'id': results['ids'][i],
                'conversation_id': metadata['conversation_id'],
                'type': metadata['type'],
                'timestamp': metadata['timestamp'],
                'text': results['documents'][i][:200] + '...' if len(results['documents'][i]) > 200 else results['documents'][i]
            })
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_entries = filtered_entries[start_idx:end_idx]
        
        return MemoryViewerResponse(
            entries=paginated_entries,
            total=len(filtered_entries),
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error retrieving memory entries: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve memory entries: {str(e)}"
        )

# Add a redirect from /memory to /memory_viewer
@app.get("/memory", include_in_schema=False)
async def redirect_to_memory_viewer():
    return RedirectResponse(url="/memory_viewer")

################################################## Link Routes ##################################################
@app.get("/links", response_model=Dict[str, List[LinkResponse]])
async def list_links():
    """Get a list of all processed links."""
    try:
        links = []
        for link_id, link_data in chatbot.links.items():
            links.append(LinkResponse(
                id=link_id,
                url=link_data['url'],
                title=link_data['title'],
                description=link_data['description'],
                content=link_data['content'],
                timestamp=link_data['timestamp']
            ))
        return {"links": links}
    except Exception as e:
        logger.error(f"Error listing links: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/link_upload", response_model=Dict[str, Any])
async def process_link(request: LinkRequest):
    try:        
        # Validate URL
        if not request.url or not isinstance(request.url, str):
            raise HTTPException(status_code=400, detail="Invalid URL provided")
            
        # Extract and store link data
        link_data = await chatbot.extract_data_from_web_page(request.url)
        
        # More comprehensive URL sanitization
        sanitized_url = (
            request.url
            .replace('://', '_')
            .replace('/', '_')
            .replace(':', '_')
            .replace('?', '_')
            .replace('&', '_')
            .replace('=', '_')
            .replace('+', '_')
            .replace('@', '_')
            .replace('#', '_')
            .replace('%', '_')
            .replace('*', '_')
            .replace('|', '_')
            .replace('\\', '_')
            .replace('"', '_')
            .replace("'", '_')
            .replace('<', '_')
            .replace('>', '_')
            .replace(' ', '_')
        )
        
        # Ensure the sanitized URL is not empty
        if not sanitized_url:
            raise HTTPException(status_code=400, detail="URL could not be sanitized properly")
            
        # Create a unique identifier
        timestamp = datetime.utcnow().timestamp()
        link_id = f"{sanitized_url}_{timestamp}"
        
        # Prepare link data
        link_data = {
            'url': request.url,
            'title': link_data['title'],
            'description': link_data['description'],
            'image': link_data.get('image'),
            'content': link_data.get('content', ''),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Store link using the Chatbot class method
        chatbot.persist_link(link_id, link_data)
        
        # Store in memory
        chatbot.links[link_id] = link_data
        
        # Track link share in analytics
        try:
            domain = request.url.split('/')[2]  # Extract domain from URL
            analytics_service.track_link_share('default', domain, 'anonymous')
        except Exception as e:
            logger.warning(f"Failed to track link share: {str(e)}")
        
        return {
            "message": "Link processed successfully",
            "link": {
                "id": link_id,
                "title": link_data['title'],
                "description": link_data['description'],
                "image": link_data.get('image'),
                "timestamp": link_data['timestamp']
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing link: {str(e)}", exc_info=True)
        analytics_service.track_error("link_upload_error")
        raise HTTPException(status_code=500, detail=f"Failed to process link: {str(e)}")

@app.post("/link_delete", response_model=Dict[str, str])
async def delete_link(request: dict = Body(...)):
    try:
        filename = request.get('filename')
        if not filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        # Get the full path to the link directory
        link_dir = os.path.join(os.getcwd(), LINKS_FOLDER, filename)
        
        # Check if the directory exists
        if not os.path.exists(link_dir):
            raise HTTPException(status_code=404, detail="Link not found")
            
        # Remove from memory first
        if filename in chatbot.links:
            del chatbot.links[filename]
        
        # Remove from disk
        import shutil
        try:
            shutil.rmtree(link_dir)
            logger.info(f"Successfully deleted link directory: {link_dir}")
        except Exception as e:
            logger.error(f"Error deleting link directory {link_dir}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete link directory: {str(e)}")
        
        return {"response": "Link deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_link: {e}")
        raise HTTPException(status_code=500, detail=str(e))

################################################## Image Routes ##################################################
@app.post("/generate_image", response_model=ImageResponse)
async def generate_image(request: ImageRequest):
    try:
        image_generator = ImageGenerator()
        result = await image_generator.generate_image(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            width=request.width,
            height=request.height,
            seed=request.seed
        )
        
        return {
            "image_url": result["image_url"],
            "metadata": {
                "prompt": request.prompt,
                "negative_prompt": request.negative_prompt,
                "num_inference_steps": request.num_inference_steps,
                "guidance_scale": request.guidance_scale,
                "width": request.width,
                "height": request.height,
                "seed": request.seed,
                "generation_time": result["generation_time"]
            }
        }
    except Exception as e:
        logger.error(f"Image generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Image generation failed")

################################################## Analytics Routes ##################################################
# Analytics endpoints
@app.get("/analytics/chat")
async def get_chat_analytics(chat_id: Optional[str] = None):
    stats = analytics_service.get_chat_statistics(chat_id)
    return stats

@app.get("/analytics/documents")
async def get_document_analytics(chat_id: Optional[str] = None):
    stats = analytics_service.get_document_statistics(chat_id)
    return stats

@app.get("/analytics/links")
async def get_link_analytics(chat_id: Optional[str] = None):
    stats = analytics_service.get_link_statistics(chat_id)
    return stats

@app.get("/analytics/usage")
async def get_usage_analytics():
    stats = analytics_service.get_usage_statistics()
    return stats

################################################## Main ##################################################
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)