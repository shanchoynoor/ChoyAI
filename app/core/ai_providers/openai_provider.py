"""
OpenAI/ChatGPT Provider

Implementation for OpenAI's GPT models including GPT-4 and GPT-3.5.
"""

import aiohttp
import asyncio
import time
from typing import List, Dict, Any, Optional

from .base_provider import BaseAIProvider, AIMessage, AIResponse, TaskType
from app.utils.logger import log_integration_activity


class OpenAIProvider(BaseAIProvider):
    """OpenAI/ChatGPT provider implementation"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        self.base_url = "https://api.openai.com/v1"
        self.api_key = config['api_key']
        self.model = config.get('model', 'gpt-4')
        self.max_tokens = config.get('max_tokens', 4000)
        self.temperature = config.get('temperature', 0.7)
        self.timeout = config.get('timeout', 30)
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.max_retries = 3
        self.base_delay = 1.0
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Define supported tasks and models
        self.supported_tasks = [
            TaskType.CONVERSATION,
            TaskType.CREATIVE,
            TaskType.PROBLEM_SOLVING,
            TaskType.ANALYSIS,
            TaskType.CODE_GENERATION,
            TaskType.SUMMARIZATION,
            TaskType.TRANSLATION
        ]
        
        self.models = {
            'default': 'gpt-4',
            'conversation': {'primary': 'gpt-4', 'fallback': 'gpt-3.5-turbo'},
            'creative': {'primary': 'gpt-4', 'fallback': 'gpt-3.5-turbo'},
            'problem_solving': {'primary': 'gpt-4', 'fallback': 'gpt-3.5-turbo'},
            'analysis': {'primary': 'gpt-4', 'fallback': 'gpt-3.5-turbo'},
            'code_generation': {'primary': 'gpt-4', 'fallback': 'gpt-3.5-turbo'},
            'summarization': {'primary': 'gpt-3.5-turbo', 'fallback': 'gpt-4'},
            'translation': {'primary': 'gpt-3.5-turbo', 'fallback': 'gpt-4'}
        }
        
    async def initialize(self) -> bool:
        """Initialize the OpenAI provider"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self.headers
            )
            
            health_ok = await self.health_check()
            if health_ok:
                self.is_available = True
                self.logger.info("OpenAI provider initialized successfully")
            else:
                self.logger.error("OpenAI provider health check failed")
                
            return health_ok
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI provider: {e}")
            return False
            
    async def chat_completion(
        self,
        messages: List[AIMessage],
        task_type: TaskType = TaskType.CONVERSATION,
        **kwargs
    ) -> AIResponse:
        """Generate chat completion using OpenAI API"""
        
        if not self.session:
            await self.initialize()
            
        # Convert AIMessage to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Select best model for task
        model = kwargs.get('model') or self.get_best_model_for_task(task_type) or self.model
        
        payload = {
            "model": model,
            "messages": openai_messages,
            "temperature": kwargs.get('temperature', self.temperature),
            "max_tokens": kwargs.get('max_tokens', self.max_tokens)
        }
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                async with self.session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload
                ) as response:
                    
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        log_integration_activity(
                            integration="openai",
                            action="chat_completion",
                            success=True,
                            response_time=response_time,
                            metadata={
                                "model": model,
                                "task_type": task_type.value,
                                "tokens_used": data.get("usage", {}).get("total_tokens", 0)
                            }
                        )
                        
                        return AIResponse(
                            content=data["choices"][0]["message"]["content"],
                            provider="openai",
                            model=model,
                            usage=data.get("usage", {}),
                            metadata={
                                "response_time": response_time,
                                "task_type": task_type.value
                            }
                        )
                        
                    else:
                        error_data = await response.text()
                        self.logger.warning(
                            f"OpenAI API error (attempt {attempt + 1}): "
                            f"Status {response.status}, Response: {error_data}"
                        )
                        
                        if attempt == self.max_retries - 1:
                            return AIResponse(
                                content="",
                                provider="openai",
                                model=model,
                                usage={},
                                error=f"API error: {response.status} - {error_data}"
                            )
                            
            except asyncio.TimeoutError:
                self.logger.warning(f"OpenAI API timeout (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    return AIResponse(
                        content="",
                        provider="openai",
                        model=model,
                        usage={},
                        error="Request timeout"
                    )
                    
            except Exception as e:
                self.logger.error(f"OpenAI API error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return AIResponse(
                        content="",
                        provider="openai",
                        model=model,
                        usage={},
                        error=str(e)
                    )
                    
            # Exponential backoff
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                
    async def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models"""
        try:
            async with self.session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    # Filter for chat models
                    chat_models = [
                        model["id"] for model in data.get("data", [])
                        if "gpt" in model["id"] and "instruct" not in model["id"]
                    ]
                    return chat_models
                else:
                    return ["gpt-4", "gpt-3.5-turbo"]
        except Exception as e:
            self.logger.error(f"Failed to get OpenAI models: {e}")
            return ["gpt-4", "gpt-3.5-turbo"]
            
    async def health_check(self) -> bool:
        """Check if OpenAI provider is healthy"""
        try:
            if not self.session:
                return False
                
            # Test with a simple completion
            test_messages = [{"role": "user", "content": "Hi"}]
            
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": test_messages,
                    "max_tokens": 5,
                    "temperature": 0.1
                }
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"OpenAI health check failed: {e}")
            return False
            
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
