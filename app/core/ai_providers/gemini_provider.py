"""
Google Gemini Provider

Implementation for Google's Gemini models.
"""

import aiohttp
import asyncio
import time
from typing import List, Dict, Any, Optional

from .base_provider import BaseAIProvider, AIMessage, AIResponse, TaskType
from app.utils.logger import log_integration_activity


class GeminiProvider(BaseAIProvider):
    """Google Gemini provider implementation"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.api_key = config['api_key']
        self.model = config.get('model', 'gemini-pro')
        self.max_tokens = config.get('max_tokens', 4000)
        self.temperature = config.get('temperature', 0.7)
        self.timeout = config.get('timeout', 30)
        
        self.max_retries = 3
        self.base_delay = 1.0
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Define supported tasks and models
        self.supported_tasks = [
            TaskType.CONVERSATION,
            TaskType.RESEARCH,
            TaskType.TRANSLATION,
            TaskType.SUMMARIZATION,
            TaskType.ANALYSIS,
            TaskType.CREATIVE,
            TaskType.PROBLEM_SOLVING
        ]
        
        self.models = {
            'default': 'gemini-pro',
            'conversation': {'primary': 'gemini-pro'},
            'research': {'primary': 'gemini-pro'},
            'translation': {'primary': 'gemini-pro'},
            'summarization': {'primary': 'gemini-pro'},
            'analysis': {'primary': 'gemini-pro'},
            'creative': {'primary': 'gemini-pro'},
            'problem_solving': {'primary': 'gemini-pro'}
        }
        
    async def initialize(self) -> bool:
        """Initialize the Gemini provider"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
            
            health_ok = await self.health_check()
            if health_ok:
                self.is_available = True
                self.logger.info("Gemini provider initialized successfully")
            else:
                self.logger.error("Gemini provider health check failed")
                
            return health_ok
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini provider: {e}")
            return False
            
    async def chat_completion(
        self,
        messages: List[AIMessage],
        task_type: TaskType = TaskType.CONVERSATION,
        **kwargs
    ) -> AIResponse:
        """Generate chat completion using Google Gemini API"""
        
        if not self.session:
            await self.initialize()
            
        # Convert AIMessage to Gemini format
        # Gemini uses a different format - combine all messages into a single prompt
        prompt_parts = []
        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")
        
        prompt = "\n\n".join(prompt_parts)
        
        # Select best model for task
        model = kwargs.get('model') or self.get_best_model_for_task(task_type) or self.model
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": kwargs.get('temperature', self.temperature),
                "maxOutputTokens": kwargs.get('max_tokens', self.max_tokens)
            }
        }
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
                
                async with self.session.post(url, json=payload) as response:
                    
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        log_integration_activity(
                            integration="gemini",
                            action="chat_completion",
                            success=True,
                            response_time=response_time,
                            metadata={
                                "model": model,
                                "task_type": task_type.value
                            }
                        )
                        
                        # Extract content from Gemini response
                        content = ""
                        if data.get("candidates") and len(data["candidates"]) > 0:
                            candidate = data["candidates"][0]
                            if candidate.get("content") and candidate["content"].get("parts"):
                                content = candidate["content"]["parts"][0].get("text", "")
                        
                        return AIResponse(
                            content=content,
                            provider="gemini",
                            model=model,
                            usage=data.get("usageMetadata", {}),
                            metadata={
                                "response_time": response_time,
                                "task_type": task_type.value
                            }
                        )
                        
                    else:
                        error_data = await response.text()
                        self.logger.warning(
                            f"Gemini API error (attempt {attempt + 1}): "
                            f"Status {response.status}, Response: {error_data}"
                        )
                        
                        if attempt == self.max_retries - 1:
                            return AIResponse(
                                content="",
                                provider="gemini",
                                model=model,
                                usage={},
                                error=f"API error: {response.status} - {error_data}"
                            )
                            
            except asyncio.TimeoutError:
                self.logger.warning(f"Gemini API timeout (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    return AIResponse(
                        content="",
                        provider="gemini",
                        model=model,
                        usage={},
                        error="Request timeout"
                    )
                    
            except Exception as e:
                self.logger.error(f"Gemini API error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return AIResponse(
                        content="",
                        provider="gemini",
                        model=model,
                        usage={},
                        error=str(e)
                    )
                    
            # Exponential backoff
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                
    async def get_available_models(self) -> List[str]:
        """Get list of available Gemini models"""
        try:
            url = f"{self.base_url}/models?key={self.api_key}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    models = []
                    for model in data.get("models", []):
                        model_name = model.get("name", "").replace("models/", "")
                        if "gemini" in model_name.lower():
                            models.append(model_name)
                    return models if models else ["gemini-pro"]
                else:
                    return ["gemini-pro"]
        except Exception as e:
            self.logger.error(f"Failed to get Gemini models: {e}")
            return ["gemini-pro"]
            
    async def health_check(self) -> bool:
        """Check if Gemini provider is healthy"""
        try:
            if not self.session:
                return False
                
            # Test with a simple generation
            test_payload = {
                "contents": [{"parts": [{"text": "Hi"}]}],
                "generationConfig": {"maxOutputTokens": 5, "temperature": 0.1}
            }
            
            url = f"{self.base_url}/models/gemini-pro:generateContent?key={self.api_key}"
            
            async with self.session.post(url, json=test_payload) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Gemini health check failed: {e}")
            return False
            
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
