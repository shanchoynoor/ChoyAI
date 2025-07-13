"""
Anthropic Claude AI Provider

Implementation for Anthropic's Claude models.
"""

import aiohttp
import asyncio
import time
from typing import List, Dict, Any, Optional

from .base_provider import BaseAIProvider, AIMessage, AIResponse, TaskType
from app.utils.logger import log_integration_activity


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        self.base_url = "https://api.anthropic.com/v1"
        self.api_key = config['api_key']
        self.model = config.get('model', 'claude-3-sonnet-20240229')
        self.max_tokens = config.get('max_tokens', 4000)
        self.temperature = config.get('temperature', 0.7)
        self.timeout = config.get('timeout', 30)
        
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        self.max_retries = 3
        self.base_delay = 1.0
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Define supported tasks and models
        self.supported_tasks = [
            TaskType.CONVERSATION,
            TaskType.ANALYSIS,
            TaskType.EMOTIONAL_SUPPORT,
            TaskType.SUMMARIZATION,
            TaskType.CREATIVE,
            TaskType.PROBLEM_SOLVING,
            TaskType.RESEARCH
        ]
        
        self.models = {
            'default': 'claude-3-sonnet-20240229',
            'conversation': {'primary': 'claude-3-sonnet-20240229'},
            'analysis': {'primary': 'claude-3-opus-20240229', 'fallback': 'claude-3-sonnet-20240229'},
            'emotional_support': {'primary': 'claude-3-sonnet-20240229'},
            'summarization': {'primary': 'claude-3-haiku-20240307', 'fallback': 'claude-3-sonnet-20240229'},
            'creative': {'primary': 'claude-3-opus-20240229', 'fallback': 'claude-3-sonnet-20240229'},
            'problem_solving': {'primary': 'claude-3-opus-20240229', 'fallback': 'claude-3-sonnet-20240229'},
            'research': {'primary': 'claude-3-opus-20240229', 'fallback': 'claude-3-sonnet-20240229'}
        }
        
    async def initialize(self) -> bool:
        """Initialize the Anthropic provider"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self.headers
            )
            
            health_ok = await self.health_check()
            if health_ok:
                self.is_available = True
                self.logger.info("Anthropic provider initialized successfully")
            else:
                self.logger.error("Anthropic provider health check failed")
                
            return health_ok
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Anthropic provider: {e}")
            return False
            
    async def chat_completion(
        self,
        messages: List[AIMessage],
        task_type: TaskType = TaskType.CONVERSATION,
        **kwargs
    ) -> AIResponse:
        """Generate chat completion using Anthropic Claude API"""
        
        if not self.session:
            await self.initialize()
            
        # Convert AIMessage to Anthropic format
        # Anthropic requires separating system message from user/assistant messages
        system_message = ""
        claude_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                claude_messages.append({"role": msg.role, "content": msg.content})
        
        # Select best model for task
        model = kwargs.get('model') or self.get_best_model_for_task(task_type) or self.model
        
        payload = {
            "model": model,
            "max_tokens": kwargs.get('max_tokens', self.max_tokens),
            "temperature": kwargs.get('temperature', self.temperature),
            "messages": claude_messages
        }
        
        if system_message:
            payload["system"] = system_message
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                async with self.session.post(
                    f"{self.base_url}/messages",
                    json=payload
                ) as response:
                    
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        log_integration_activity(
                            integration="anthropic",
                            action="chat_completion",
                            success=True,
                            response_time=response_time,
                            metadata={
                                "model": model,
                                "task_type": task_type.value,
                                "tokens_used": data.get("usage", {}).get("output_tokens", 0)
                            }
                        )
                        
                        # Extract content from Claude response
                        content = ""
                        if data.get("content") and len(data["content"]) > 0:
                            content = data["content"][0].get("text", "")
                        
                        return AIResponse(
                            content=content,
                            provider="anthropic",
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
                            f"Anthropic API error (attempt {attempt + 1}): "
                            f"Status {response.status}, Response: {error_data}"
                        )
                        
                        if attempt == self.max_retries - 1:
                            return AIResponse(
                                content="",
                                provider="anthropic",
                                model=model,
                                usage={},
                                error=f"API error: {response.status} - {error_data}"
                            )
                            
            except asyncio.TimeoutError:
                self.logger.warning(f"Anthropic API timeout (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    return AIResponse(
                        content="",
                        provider="anthropic",
                        model=model,
                        usage={},
                        error="Request timeout"
                    )
                    
            except Exception as e:
                self.logger.error(f"Anthropic API error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return AIResponse(
                        content="",
                        provider="anthropic",
                        model=model,
                        usage={},
                        error=str(e)
                    )
                    
            # Exponential backoff
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                
    async def get_available_models(self) -> List[str]:
        """Get list of available Anthropic models"""
        # Anthropic doesn't have a models endpoint, return known models
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
            
    async def health_check(self) -> bool:
        """Check if Anthropic provider is healthy"""
        try:
            if not self.session:
                return False
                
            # Test with a simple completion
            test_payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 10,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": "Hi"}]
            }
            
            async with self.session.post(
                f"{self.base_url}/messages",
                json=test_payload
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Anthropic health check failed: {e}")
            return False
            
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
