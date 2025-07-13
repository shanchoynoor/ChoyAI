"""
DeepSeek AI Provider

Implementation of DeepSeek API provider with enhanced features.
Migrated from utils/deepseek_api.py to the new provider system.
"""

import aiohttp
import asyncio
import time
from typing import List, Dict, Any, Optional

from .base_provider import BaseAIProvider, AIMessage, AIResponse, TaskType
from app.utils.logger import log_integration_activity, performance_monitor


class DeepSeekProvider(BaseAIProvider):
    """DeepSeek AI provider implementation"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        self.base_url = "https://api.deepseek.com/v1"
        self.api_key = config['api_key']
        self.model = config.get('model', 'deepseek-chat')
        self.max_tokens = config.get('max_tokens', 4000)
        self.temperature = config.get('temperature', 0.7)
        self.timeout = config.get('timeout', 30)
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # DeepSeek specific configuration
        self.max_retries = 3
        self.base_delay = 1.0
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Define supported tasks and models
        self.supported_tasks = [
            TaskType.CONVERSATION,
            TaskType.TECHNICAL,
            TaskType.CODE_GENERATION,
            TaskType.ANALYSIS,
            TaskType.PROBLEM_SOLVING,
            TaskType.SUMMARIZATION
        ]
        
        self.models = {
            'default': 'deepseek-chat',
            'conversation': {'primary': 'deepseek-chat'},
            'technical': {'primary': 'deepseek-coder'},
            'code_generation': {'primary': 'deepseek-coder'},
            'analysis': {'primary': 'deepseek-chat'},
            'problem_solving': {'primary': 'deepseek-chat'},
            'summarization': {'primary': 'deepseek-chat'}
        }
        
    async def initialize(self) -> bool:
        """Initialize the DeepSeek provider"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self.headers
            )
            
            # Test connection
            health_ok = await self.health_check()
            if health_ok:
                self.is_available = True
                self.logger.info("DeepSeek provider initialized successfully")
            else:
                self.logger.error("DeepSeek provider health check failed")
                
            return health_ok
            
        except Exception as e:
            self.logger.error(f"Failed to initialize DeepSeek provider: {e}")
            return False
            
    async def chat_completion(
        self,
        messages: List[AIMessage],
        task_type: TaskType = TaskType.CONVERSATION,
        **kwargs
    ) -> AIResponse:
        """Generate chat completion using DeepSeek API"""
        
        if not self.session:
            await self.initialize()
            
        # Convert AIMessage to DeepSeek format
        deepseek_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Select best model for task
        model = kwargs.get('model') or self.get_best_model_for_task(task_type) or self.model
        
        payload = {
            "model": model,
            "messages": deepseek_messages,
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
                        
                        # Log successful interaction
                        log_integration_activity(
                            integration="deepseek",
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
                            provider="deepseek",
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
                            f"DeepSeek API error (attempt {attempt + 1}): "
                            f"Status {response.status}, Response: {error_data}"
                        )
                        
                        if attempt == self.max_retries - 1:
                            return AIResponse(
                                content="",
                                provider="deepseek",
                                model=model,
                                usage={},
                                error=f"API error: {response.status} - {error_data}"
                            )
                            
            except asyncio.TimeoutError:
                self.logger.warning(f"DeepSeek API timeout (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    return AIResponse(
                        content="",
                        provider="deepseek",
                        model=model,
                        usage={},
                        error="Request timeout"
                    )
                    
            except Exception as e:
                self.logger.error(f"DeepSeek API error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return AIResponse(
                        content="",
                        provider="deepseek",
                        model=model,
                        usage={},
                        error=str(e)
                    )
                    
            # Exponential backoff
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                
    async def get_available_models(self) -> List[str]:
        """Get list of available DeepSeek models"""
        try:
            async with self.session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    return [model["id"] for model in data.get("data", [])]
                else:
                    # Return known models if API call fails
                    return ["deepseek-chat", "deepseek-coder"]
        except Exception as e:
            self.logger.error(f"Failed to get DeepSeek models: {e}")
            return ["deepseek-chat", "deepseek-coder"]
            
    async def health_check(self) -> bool:
        """Check if DeepSeek provider is healthy"""
        try:
            if not self.session:
                return False
                
            # Simple API test
            test_messages = [{"role": "user", "content": "Hi"}]
            
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": test_messages,
                    "max_tokens": 10,
                    "temperature": 0.1
                }
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"DeepSeek health check failed: {e}")
            return False
            
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
