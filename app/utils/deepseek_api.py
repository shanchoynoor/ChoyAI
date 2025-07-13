"""
Enhanced DeepSeek API client for Choy AI Brain

Provides async chat completions with retry logic and better error handling
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
import aiohttp
import time

from app.config.settings import settings
from app.utils.logger import log_integration_activity, performance_monitor


class DeepSeekAPI:
    """Enhanced DeepSeek API client"""
    
    def __init__(self):
        self.base_url = "https://api.deepseek.com/v1"
        self.api_key = settings.deepseek_api_key.get_secret_value()
        self.model = settings.deepseek_model
        self.max_tokens = settings.deepseek_max_tokens
        self.temperature = settings.deepseek_temperature
        self.timeout = settings.response_timeout
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting and retry
        self.max_retries = 3
        self.base_delay = 1.0
        
        # Session for connection pooling
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """Ensure session exists"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self.headers
            )
    
    @performance_monitor("deepseek_chat_completion")
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate chat completion using DeepSeek API
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum tokens in response
            model: Model to use (defaults to configured model)
            
        Returns:
            API response dictionary
        """
        await self._ensure_session()
        
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
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
                        result = await response.json()
                        
                        log_integration_activity(
                            "deepseek", 
                            "chat_completion", 
                            "success",
                            f"Response time: {response_time:.2f}s, Tokens: {result.get('usage', {}).get('total_tokens', 'unknown')}"
                        )
                        
                        return result
                    
                    elif response.status == 429:  # Rate limited
                        error_text = await response.text()
                        delay = self.base_delay * (2 ** attempt)
                        
                        log_integration_activity(
                            "deepseek",
                            "chat_completion",
                            "rate_limited",
                            f"Attempt {attempt + 1}, waiting {delay}s"
                        )
                        
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(delay)
                            continue
                        else:
                            raise Exception(f"Rate limited after {self.max_retries} attempts")
                    
                    else:
                        error_text = await response.text()
                        log_integration_activity(
                            "deepseek",
                            "chat_completion", 
                            "error",
                            f"HTTP {response.status}: {error_text}"
                        )
                        
                        raise Exception(f"API error {response.status}: {error_text}")
            
            except asyncio.TimeoutError:
                log_integration_activity(
                    "deepseek",
                    "chat_completion",
                    "timeout",
                    f"Attempt {attempt + 1} timed out"
                )
                
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise Exception("Request timed out after multiple attempts")
            
            except Exception as e:
                log_integration_activity(
                    "deepseek",
                    "chat_completion",
                    "error",
                    f"Attempt {attempt + 1} failed: {str(e)}"
                )
                
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise
        
        raise Exception("All retry attempts failed")
    
    async def simple_chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Simple chat interface for single user message
        
        Args:
            user_message: User's message
            system_prompt: Optional system prompt
            temperature: Response randomness
            
        Returns:
            AI response text
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = await self.chat_completion(
                messages=messages,
                temperature=temperature
            )
            
            # Extract response text
            if 'choices' in response and len(response['choices']) > 0:
                return response['choices'][0]['message']['content'].strip()
            else:
                raise Exception("No response content in API result")
        
        except Exception as e:
            self.logger.error(f"Error in simple chat: {e}")
            raise
    
    async def conversation_chat(
        self,
        conversation_history: List[Dict[str, str]],
        new_message: str,
        system_prompt: Optional[str] = None,
        max_history: int = 10
    ) -> str:
        """
        Chat with conversation history
        
        Args:
            conversation_history: Previous messages
            new_message: New user message
            system_prompt: Optional system prompt
            max_history: Maximum history messages to include
            
        Returns:
            AI response text
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add limited conversation history
        if conversation_history:
            recent_history = conversation_history[-max_history:]
            messages.extend(recent_history)
        
        # Add new message
        messages.append({"role": "user", "content": new_message})
        
        try:
            response = await self.chat_completion(messages=messages)
            
            if 'choices' in response and len(response['choices']) > 0:
                return response['choices'][0]['message']['content'].strip()
            else:
                raise Exception("No response content in API result")
        
        except Exception as e:
            self.logger.error(f"Error in conversation chat: {e}")
            raise
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics (if available)"""
        # This would require additional API endpoints from DeepSeek
        # For now, return placeholder
        return {
            "api_calls_today": "N/A",
            "tokens_used_today": "N/A",
            "quota_remaining": "N/A"
        }
    
    async def health_check(self) -> bool:
        """Check if API is accessible"""
        try:
            response = await self.simple_chat(
                "Hello", 
                system_prompt="Respond with just 'OK'",
                temperature=0.0
            )
            return "ok" in response.lower()
        
        except Exception as e:
            self.logger.error(f"DeepSeek API health check failed: {e}")
            return False
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None


# Convenience function for simple usage
async def quick_chat(message: str, system_prompt: str = None) -> str:
    """Quick chat function for simple use cases"""
    async with DeepSeekAPI() as api:
        return await api.simple_chat(message, system_prompt)


# Export the main class
__all__ = ["DeepSeekAPI", "quick_chat"]
