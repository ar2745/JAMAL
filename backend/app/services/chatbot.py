import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import docx
import PyPDF2
import requests
from bs4 import BeautifulSoup
from werkzeug.utils import secure_filename

from .analytics import AnalyticsService
from .llm_integration import LLMIntegration, ModelType
from .memory import MemoryManager
from .response import ResponseGenerator
from .web_search import WebSearchService

logger = logging.getLogger(__name__)

class Chatbot:
    """Main class for the chatbot application."""
################################################## Chatbot Constructor ##################################################
    def __init__(
        self,
        api_url: str = "http://localhost:11434",
        storage_folder: str = "storage",
        chats_folder: str = "chats",
        uploads_folder: str = "uploads",
        links_folder: str = "links"
    ):
        """Initialize the chatbot with all required services.
        
        Args:
            api_url: Base URL for the LLM API
            chats_folder: Directory for storing chat data
            uploads_folder: Directory for storing uploaded files
            links_folder: Directory for storing processed links
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self.llm_integration = LLMIntegration(api_url)
        self.memory_manager = MemoryManager(api_url)
        self.response_generator = ResponseGenerator(self.llm_integration)
        self.analytics_service = AnalyticsService()
        self.web_search_service = WebSearchService()
        
        # Setup directories
        self.storage_folder = storage_folder
        self.chats_folder = chats_folder
        self.uploads_folder = uploads_folder
        self.links_folder = links_folder
        
        # Create directories if they don't exist
        for folder in [self.storage_folder, self.chats_folder, self.uploads_folder, self.links_folder]:
            os.makedirs(folder, exist_ok=True)
            
        # Initialize storage
        self.documents = {}
        self.links = {}
        self.load_persisted_data()

################################################## Message Processing ##################################################
    async def process_message(
        self,
        user_input: str,
        conversation_id: Optional[str] = None,
        document_name: Optional[str] = None,
        link_id: Optional[str] = None,
        is_reasoning_mode: bool = False,
        is_web_search: bool = False,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a user message and generate a response.
        
        Args:
            user_input: The user's message
            conversation_id: ID of the conversation
            document_name: Name of the document to reference
            link_id: ID of the link to reference
            is_reasoning_mode: Whether to use reasoning mode
            is_web_search: Whether to perform a web search
            user_id: ID of the user
            
        Returns:
            Dictionary containing the response and metadata
        """
        try:
            # Track user activity
            if user_id:
                self.analytics_service.track_user_activity(user_id)
            
            # Track chat activity
            chat_id = conversation_id or 'default'
            self.analytics_service.track_chat_activity(chat_id, user_id=user_id)
            
            # Get relevant memories if conversation exists
            memories = []
            if conversation_id:
                memories = await self.memory_manager.retrieve_relevant_memories(
                    conversation_id,
                    user_input
                )
            
            # Generate response based on context
            response_data = {}
            if is_web_search:
                # Perform web search and generate response
                search_results = await self.web_search_service.search_web(user_input)
                response_data = await self.response_generator.generate_web_search_response(
                    user_input,
                    search_results,
                    is_reasoning_mode
                )
            elif document_name and document_name in self.documents:
                response_data = await self.response_generator.generate_document_response(
                    user_input,
                    self.documents[document_name],
                    is_reasoning_mode
                )
            elif link_id and link_id in self.links:
                response_data = await self.response_generator.generate_link_response(
                    user_input,
                    self.links[link_id]['content'],
                    is_reasoning_mode
                )
            elif memories:
                response_data = await self.response_generator.generate_contextual_response(
                    user_input,
                    memories,
                    is_reasoning_mode
                )
            else:
                if is_reasoning_mode:
                    response_data = await self.response_generator.generate_reasoned_response(user_input)
                else:
                    response_data = await self.response_generator.generate_simple_response(user_input)
            
            # Ensure response_data is a string
            if isinstance(response_data, dict):
                response_text = response_data.get('text', '')
            else:
                response_text = str(response_data)
            
            # Track response time
            self.analytics_service.track_response_time(0)  # We'll need to track this differently
            
            # Store the conversation in memory
            if conversation_id:
                await self.memory_manager.store_memory(
                    conversation_id,
                    user_input,
                    response_text,
                    [document_name] if document_name else None,
                    [link_id] if link_id else None
                )
            
            return {
                'response': response_text,
                'conversation_id': conversation_id,
                'document_name': document_name,
                'link_id': link_id,
                'is_reasoning_mode': is_reasoning_mode
            }
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.analytics_service.track_error("message_processing_error")
            raise

################################################## Persistence ##################################################
    def load_persisted_data(self):
        """Load persisted documents and links from disk."""
        try:
            # Load documents
            for filename in os.listdir(self.uploads_folder):
                if filename.endswith('.meta.json'):
                    continue
                filepath = os.path.join(self.uploads_folder, filename)
                metadata_path = os.path.join(self.uploads_folder, f"{filename}.meta.json")
                
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        self.documents[filename] = metadata.get('content', '')
            
            # Load links
            for link_dir in os.listdir(self.links_folder):
                link_path = os.path.join(self.links_folder, link_dir)
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
            self.logger.error(f"Error loading persisted data: {e}")

    def persist_document(self, filename: str, content: str, metadata: dict):
        """Persist document and its metadata to disk."""
        try:
            filepath = os.path.join(self.uploads_folder, filename)
            metadata_path = os.path.join(self.uploads_folder, f"{filename}.meta.json")
            
            # Save content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Save metadata
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
        except Exception as e:
            self.logger.error(f"Error persisting document: {e}")

    def persist_link(self, link_id: str, link_data: dict):
        """Persist link and its metadata to disk."""
        try:
            # Create link directory
            link_dir = os.path.join(self.links_folder, link_id)
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
            self.logger.error(f"Error persisting link: {e}")
    
    async def close(self):
        """Clean up resources."""
        await self.llm_integration.close()

################################################## File Processing ##################################################
    def extract_text_from_pdf(self, filepath: str) -> str:
        """Extract text from PDF file."""
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

    def extract_text_from_txt(self, filepath: str) -> str:
        """Extract text from TXT file."""
        try:
            with open(filepath, 'r') as file:
                return file.read()
        except FileNotFoundError:
            return "Error file not found"
        except Exception as e:
            return f"Error: {e}"

    def extract_text_from_json(self, filepath: str) -> str:
        """Extract text from JSON file."""
        try:
            with open(filepath, 'r') as file:
                data = json.load(file)
                return json.dumps(data, indent=4)
        except FileNotFoundError:
            return "Error file not found"
        except Exception as e:
            return f"Error: {e}"

    def extract_text_from_docx(self, filepath: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(filepath)
            return "\n".join([para.text for para in doc.paragraphs])
        except FileNotFoundError:
            return "Error file not found"
        except Exception as e:
            return f"Error: {e}"

    def extract_text_from_file(self, filepath: str) -> str:
        """Extract text from various file types."""
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

################################################## Web Processing ##################################################
    def extract_metadata(self, url: str) -> Dict[str, Optional[str]]:
        """Extract metadata from a web page."""
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

    async def extract_data_from_web_page(self, url: str) -> Dict[str, Any]:
        """Extract data from a web page."""
        try:
            # Extract metadata
            metadata = self.extract_metadata(url)
            
            # Create link data structure
            link_data = {
                'url': url,
                'title': metadata.get('title'),
                'description': metadata.get('description'),
                'image': metadata.get('image'),
                'content': metadata.get('content'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return link_data
        except Exception as e:
            self.logger.error(f"Error extracting data from web page: {e}")
            raise
 