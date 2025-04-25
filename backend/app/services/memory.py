import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import chromadb

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, api_url: str = "http://localhost:11434"):
        # Remove /api/generate from the URL if it's present
        self.api_url = api_url.replace("/api/generate", "")
        self.embedding_model = "nomic-embed-text:latest"
        self.fallback_model = "nomic-embed-text:latest"  # Smaller model as fallback
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
            logger.error(f"Error initializing ChromaDB: {e}")
            raise

    async def get_embedding(self, text: str) -> List[float]:
        try:
            # First try with the main model
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_url}/api/embeddings",
                        json={
                            "model": self.embedding_model,
                            "prompt": text
                        }
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get("embedding", [])
                        elif response.status == 500 and "memory" in str(await response.text()).lower():
                            # If memory error, try fallback model
                            logger.info("Memory error, trying fallback model...")
                            async with session.post(
                                f"{self.api_url}/api/embed",
                                json={
                                    "model": self.fallback_model,
                                    "prompt": text
                                }
                            ) as fallback_response:
                                if fallback_response.status == 200:
                                    result = await fallback_response.json()
                                    return result.get("embedding", [])
                        raise Exception(f"Failed to get embedding: {response.status}")
            except Exception as e:
                logger.error(f"Error with main model: {e}")
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
            logger.error(f"Error getting embedding: {e}")
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
            document_contents = []
            link_contents = []

            # Read document contents
            if documents:
                for doc_name in documents:
                    try:
                        with open(os.path.join('documents', doc_name), 'r') as f:
                            content = f.read()
                            document_contents.append(content)
                            texts_to_embed.append(content)
                    except Exception as e:
                        logger.error(f"Error reading document {doc_name}: {e}")
                        raise

            # Read link contents
            if links:
                for link_name in links:
                    try:
                        with open(os.path.join('links', link_name), 'r') as f:
                            link_data = json.load(f)
                            content = link_data.get('content', '')
                            link_contents.append(content)
                            texts_to_embed.append(content)
                    except Exception as e:
                        logger.error(f"Error reading link {link_name}: {e}")
                        raise

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
                    logger.error(f"Error storing memory {i}: {e}")
                    raise

            return memory_entry
        except Exception as e:
            logger.error(f"Error in store_memory: {e}")
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
            logger.error(f"Error in retrieve_relevant_memories: {e}")
            raise 