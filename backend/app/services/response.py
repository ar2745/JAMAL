import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from llm_integration import LLMIntegration, ModelType

logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self, llm_integration: LLMIntegration):
        self.llm_integration = llm_integration
        self.logger = logging.getLogger(__name__)

    async def generate_simple_response(
        self,
        input_text: str,
        conversation_id: Optional[str] = None,
        stream: bool = False
    ) -> str | AsyncGenerator[str, None]:
        """Generate a simple response using the basic model."""
        try:
            return await self.llm_integration.generate_response(
                input_text,
                model_type=ModelType.SIMPLE,
                stream=stream,
                conversation_id=conversation_id
            )
        except Exception as e:
            self.logger.error(f"Error generating simple response: {e}")
            raise

    async def generate_reasoned_response(
        self,
        input_text: str,
        conversation_id: Optional[str] = None,
        stream: bool = False
    ) -> str | AsyncGenerator[str, None]:
        """Generate a reasoned response using the advanced model."""
        try:
            return await self.llm_integration.generate_response(
                input_text,
                model_type=ModelType.REASONED,
                stream=stream,
                conversation_id=conversation_id
            )
        except Exception as e:
            self.logger.error(f"Error generating reasoned response: {e}")
            raise

    async def generate_document_response(
        self,
        input_text: str,
        doc_content: str,
        conversation_id: Optional[str] = None,
        stream: bool = False,
        is_reasoning_mode: bool = False
    ) -> str | AsyncGenerator[str, None]:
        """Generate a response based on document content."""
        try:
            combined_input = f"{input_text}\n\nDocument Content:\n{doc_content}"
            if is_reasoning_mode:
                return await self.generate_reasoned_response(
                    combined_input,
                    conversation_id=conversation_id,
                    stream=stream
                )
            return await self.generate_simple_response(
                combined_input,
                conversation_id=conversation_id,
                stream=stream
            )
        except Exception as e:
            self.logger.error(f"Error generating document response: {e}")
            raise

    async def generate_link_response(
        self,
        input_text: str,
        link_content: str,
        conversation_id: Optional[str] = None,
        stream: bool = False,
        is_reasoning_mode: bool = False
    ) -> str | AsyncGenerator[str, None]:
        """Generate a response based on link content."""
        try:
            combined_input = f"{input_text}\n\nLink Content:\n{link_content}"
            if is_reasoning_mode:
                return await self.generate_reasoned_response(
                    combined_input,
                    conversation_id=conversation_id,
                    stream=stream
                )
            return await self.generate_simple_response(
                combined_input,
                conversation_id=conversation_id,
                stream=stream
            )
        except Exception as e:
            self.logger.error(f"Error generating link response: {e}")
            raise

    async def generate_combined_response(
        self,
        input_text: str,
        doc_content: Optional[str] = None,
        link_content: Optional[str] = None,
        conversation_id: Optional[str] = None,
        stream: bool = False,
        is_reasoning_mode: bool = False
    ) -> str | AsyncGenerator[str, None]:
        """Generate a response combining document and link content."""
        try:
            context_parts = []
            if doc_content:
                context_parts.append(f"Document Content:\n{doc_content}")
            if link_content:
                context_parts.append(f"Link Content:\n{link_content}")
            
            combined_input = f"{input_text}\n\n" + "\n\n".join(context_parts)
            
            if is_reasoning_mode:
                return await self.generate_reasoned_response(
                    combined_input,
                    conversation_id=conversation_id,
                    stream=stream
                )
            return await self.generate_simple_response(
                combined_input,
                conversation_id=conversation_id,
                stream=stream
            )
        except Exception as e:
            self.logger.error(f"Error generating combined response: {e}")
            raise

    async def generate_contextual_response(
        self,
        input_text: str,
        memories: List[Dict[str, Any]],
        conversation_id: Optional[str] = None,
        stream: bool = False,
        is_reasoning_mode: bool = False
    ) -> str | AsyncGenerator[str, None]:
        """Generate a response using relevant memories as context."""
        try:
            # Format memories into context
            memory_context = "\n\n".join([
                f"Memory ({mem['type']}):\n{mem['text']}"
                for mem in memories
            ])
            
            combined_input = f"{input_text}\n\nRelevant Context:\n{memory_context}"
            
            if is_reasoning_mode:
                return await self.generate_reasoned_response(
                    combined_input,
                    conversation_id=conversation_id,
                    stream=stream
                )
            return await self.generate_simple_response(
                combined_input,
                conversation_id=conversation_id,
                stream=stream
            )
        except Exception as e:
            self.logger.error(f"Error generating contextual response: {e}")
            raise

    def clear_conversation(self, conversation_id: str) -> None:
        """Clear conversation history for a given ID."""
        self.llm_integration.clear_conversation(conversation_id)

    def get_conversation_history(self, conversation_id: str) -> Optional[list]:
        """Get conversation history for a given ID."""
        return self.llm_integration.get_conversation_history(conversation_id) 