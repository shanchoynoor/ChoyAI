"""
xAI Grok Provider

Implementation for xAI's Grok models.
"""

import aiohttp
import asyncio
import time
from typing import List, Dict, Any, Optional

from .base_provider import BaseAIProvider, AIMessage, AIResponse, TaskType
from app.utils.logger import log_integration_activity


class XAIProvider(BaseAIProvider):
    """xAI Grok provider implementation"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        self.base_url = "https://api.x.ai/v1"
        self.api_key = config['api_key']
        self.model = config.get('model', 'grok-beta')
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
            TaskType.ANALYSIS,
            TaskType.PROBLEM_SOLVING,
            TaskType.RESEARCH,
            TaskType.TECHNICAL
        ]
        
        self.models = {
            'default': 'grok-beta',
            'conversation': {'primary': 'grok-beta'},
            'creative': {'primary': 'grok-beta'},
            'analysis': {'primary': 'grok-beta'},
            'problem_solving': {'primary': 'grok-beta'},
            'research': {'primary': 'grok-beta'},
            'technical': {'primary': 'grok-beta'}
        }
        
    async def initialize(self) -> bool:
        """Initialize the xAI provider"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self.headers
            )
            
            health_ok = await self.health_check()
            if health_ok:
                self.is_available = True
                self.logger.info("xAI provider initialized successfully")
            else:
                self.logger.error("xAI provider health check failed")
                
            return health_ok
            
        except Exception as e:
            self.logger.error(f"Failed to initialize xAI provider: {e}")
            return False
            
    async def chat_completion(
        self,
        messages: List[AIMessage],
        task_type: TaskType = TaskType.CONVERSATION,
        **kwargs
    ) -> AIResponse:
        """Generate chat completion using xAI Grok API"""
        
        if not self.session:
            await self.initialize()
            
        # Convert AIMessage to xAI format
        xai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Select best model for task
        model = kwargs.get('model') or self.get_best_model_for_task(task_type) or self.model
        
        payload = {
            "model": model,
            "messages": xai_messages,
            "temperature": kwargs.get('temperature', self.temperature),
            "max_tokens": kwargs.get('max_tokens', self.max_tokens),
            "stream": False
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
                            integration="xai",
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
                            provider="xai",
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
                            f"xAI API error (attempt {attempt + 1}): "
                            f"Status {response.status}, Response: {error_data}"
                        )
                        
                        if attempt == self.max_retries - 1:
                            return AIResponse(
                                content="",
                                provider="xai",
                                model=model,
                                usage={},
                                error=f"API error: {response.status} - {error_data}"
                            )
                            
            except asyncio.TimeoutError:
                self.logger.warning(f"xAI API timeout (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    return AIResponse(
                        content="",
                        provider="xai",
                        model=model,
                        usage={},
                        error="Request timeout"
                    )
                    
            except Exception as e:
                self.logger.error(f"xAI API error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return AIResponse(
                        content="",
                        provider="xai",
                        model=model,
                        usage={},
                        error=str(e)
                    )
                    
            # Exponential backoff
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                
    async def get_available_models(self) -> List[str]:
        """Get list of available xAI models"""
        try:
            async with self.session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    return [model["id"] for model in data.get("data", [])]
                else:
                    return ["grok-beta"]
        except Exception as e:
            self.logger.error(f"Failed to get xAI models: {e}")
            return ["grok-beta"]
            
    async def health_check(self) -> bool:
        """Check if xAI provider is healthy"""
        try:
            if not self.session:
                return False
                
            # Test with a simple completion
            test_messages = [{"role": "user", "content": "Hi"}]
            
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": test_messages,
                    "max_tokens": 5,
                    "temperature": 0.1
                }
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"xAI health check failed: {e}")
            return False
            
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
