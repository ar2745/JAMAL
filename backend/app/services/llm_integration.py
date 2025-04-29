import asyncio
import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Generator, Optional

import aiohttp


class ModelType(Enum):
    SIMPLE = "gemma3:1b"
    REASONED = "deepseek-r1:1.5b"

@dataclass
class ModelConfig:
    name: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

class LLMIntegration:
    def __init__(self, api_url: str = "http://localhost:11434/api/generate"):
        self.api_url = api_url
        self.models = {
            ModelType.SIMPLE: ModelConfig(name="llama3.2:1B"),
            ModelType.REASONED: ModelConfig(name="deepseek-r1:1.5b")
        }
        self.conversation_history: Dict[str, list] = {}
        self.max_retries = 3
        self.retry_delay = 1

    async def check_model_health(self, model_name: str) -> bool:
        """Check if the model is available and responding."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json={"model": model_name, "prompt": "test", "stream": False}
                ) as response:
                    return response.status == 200
        except:
            return False

    def _prepare_prompt(self, prompt: str, context: Optional[list] = None) -> str:
        """Prepare the prompt with context if available."""
        if context:
            context_str = "\n".join([f"{'User' if i % 2 == 0 else 'Assistant'}: {msg}" 
                                    for i, msg in enumerate(context)])
            return f"Context:\n{context_str}\n\nUser: {prompt}\nAssistant:"
        return prompt

    async def generate_response(
        self,
        prompt: str,
        model_type: ModelType = ModelType.REASONED,
        stream: bool = False,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a response with enhanced features."""
        model_config = self.models[model_type]
        
        # Get conversation history if available
        context = self.conversation_history.get(conversation_id, []) if conversation_id else None
        
        # Prepare the prompt with context
        prepared_prompt = self._prepare_prompt(prompt, context)
        
        # Prepare request data
        data = {
            "model": model_config.name,
            "prompt": prepared_prompt,
            "stream": stream,
            "temperature": kwargs.get('temperature', model_config.temperature),
            "max_tokens": kwargs.get('max_tokens', model_config.max_tokens),
            "top_p": kwargs.get('top_p', model_config.top_p),
            "frequency_penalty": kwargs.get('frequency_penalty', model_config.frequency_penalty),
            "presence_penalty": kwargs.get('presence_penalty', model_config.presence_penalty)
        }

        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    if stream:
                        async def stream_response():
                            async with session.post(self.api_url, json=data) as response:
                                if response.status == 200:
                                    async for line in response.content:
                                        if line:
                                            try:
                                                json_response = line.decode('utf-8')
                                                if json_response.startswith('data: '):
                                                    json_response = json_response[6:]
                                                response_data = json.loads(json_response)
                                                if 'response' in response_data:
                                                    yield response_data['response']
                                            except Exception as e:
                                                print(f"Error processing stream: {e}")
                                                continue
                        return stream_response()
                    else:
                        async with session.post(self.api_url, json=data) as response:
                            if response.status == 200:
                                result = (await response.json()).get("response", "")
                                
                                # Update conversation history if available
                                if conversation_id:
                                    if conversation_id not in self.conversation_history:
                                        self.conversation_history[conversation_id] = []
                                    self.conversation_history[conversation_id].extend([prompt, result])
                                    # Keep only last 10 exchanges
                                    if len(self.conversation_history[conversation_id]) > 20:
                                        self.conversation_history[conversation_id] = self.conversation_history[conversation_id][-20:]
                                
                                return result
                            else:
                                raise Exception(f"API returned status code {response.status}")
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Failed after {self.max_retries} attempts: {str(e)}")
                await asyncio.sleep(self.retry_delay * (attempt + 1))

    def clear_conversation(self, conversation_id: str) -> None:
        """Clear conversation history for a given ID."""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]

    def get_conversation_history(self, conversation_id: str) -> Optional[list]:
        """Get conversation history for a given ID."""
        return self.conversation_history.get(conversation_id)

# Example usage:
"""
llm = LLMIntegration()
# Simple response
response = await llm.generate_response("What is the capital of France?", ModelType.SIMPLE)

# Streamed reasoned response with context
async for chunk in llm.generate_response(
    "What was the previous capital?",
    ModelType.REASONED,
    stream=True,
    conversation_id="user123"
):
    print(chunk, end="", flush=True)
"""