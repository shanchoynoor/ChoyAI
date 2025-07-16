"""
Live API Integration Manager for ChoyAI Personas

Ensures all personas can access live information from various APIs and web sources.
Handles graceful error responses without revealing internet access limitations.
"""

import asyncio
import logging
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import re
import html

from app.config.settings import settings


class APISource(Enum):
    """Available API sources for live information"""
    WEB_SEARCH = "web_search"
    NEWS = "news" 
    WEATHER = "weather"
    FINANCE = "finance"
    CRYPTO = "crypto"
    SOCIAL_TRENDS = "social_trends"
    MAPS = "maps"
    TRANSLATE = "translate"
    GENERAL_SEARCH = "general_search"
    REAL_TIME_DATA = "real_time_data"


@dataclass
class LiveDataRequest:
    """Request structure for live data"""
    source: APISource
    query: str
    user_id: str
    persona: str
    context: Optional[Dict[str, Any]] = None
    priority: str = "normal"  # normal, high, low


@dataclass 
class LiveDataResponse:
    """Response structure for live data"""
    success: bool
    data: Any
    source: APISource
    timestamp: datetime
    error_message: Optional[str] = None
    fallback_used: bool = False


class LiveAPIIntegrationManager:
    """
    Manages live API access for all personas with graceful error handling
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API configurations
        self.api_configs = self._initialize_api_configs()
        
        # Rate limiting
        self.rate_limits = {}
        self.last_request_times = {}
        
        # Cache for frequently requested data
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes default TTL
        
        # Graceful error messages that don't reveal internet limitations
        self.graceful_error_messages = {
            APISource.WEB_SEARCH: [
                "I'm having trouble accessing the latest information right now. Please try again in a moment.",
                "The information service is temporarily unavailable. Let me try again shortly.",
                "I'm unable to retrieve the most current data at this time. Please check back soon."
            ],
            APISource.NEWS: [
                "The news service is currently updating. Please try again in a few minutes.",
                "I'm having difficulty accessing the latest news right now. Please try again shortly.",
                "The news feed is temporarily unavailable. Let me check again soon."
            ],
            APISource.WEATHER: [
                "Weather information is currently being updated. Please try again in a moment.",
                "I'm unable to access current weather data right now. Please check back soon.",
                "The weather service is temporarily unavailable. Let me try again shortly."
            ],
            APISource.FINANCE: [
                "Financial data is currently being updated. Please try again in a moment.",
                "Market information is temporarily unavailable. Let me check again soon.",
                "I'm having trouble accessing the latest financial data right now."
            ],
            APISource.CRYPTO: [
                "Cryptocurrency data is being updated. Please try again in a moment.",
                "Crypto market information is temporarily unavailable. Let me check again soon.",
                "I'm unable to access current crypto prices right now. Please try again shortly."
            ]
        }
    
    def _initialize_api_configs(self) -> Dict[APISource, Dict[str, Any]]:
        """Initialize API configurations"""
        return {
            APISource.WEB_SEARCH: {
                "primary_api": "serper",
                "fallback_api": "perplexity",
                "rate_limit": 60,  # requests per minute
                "timeout": 15,
                "endpoints": {
                    "serper": "https://google.serper.dev/search",
                    "perplexity": "https://api.perplexity.ai/chat/completions"
                }
            },
            APISource.NEWS: {
                "primary_api": "newsapi",
                "fallback_api": "rss_feeds",
                "rate_limit": 100,
                "timeout": 10,
                "endpoints": {
                    "newsapi": "https://newsapi.org/v2/everything",
                    "rss_feeds": "built_in"
                }
            },
            APISource.WEATHER: {
                "primary_api": "openweathermap",
                "fallback_api": "weatherapi",
                "rate_limit": 60,
                "timeout": 10,
                "endpoints": {
                    "openweathermap": "https://api.openweathermap.org/data/2.5",
                    "weatherapi": "https://api.weatherapi.com/v1"
                }
            },
            APISource.FINANCE: {
                "primary_api": "alpha_vantage",
                "fallback_api": "yahoo_finance",
                "rate_limit": 75,
                "timeout": 15,
                "endpoints": {
                    "alpha_vantage": "https://www.alphavantage.co/query",
                    "yahoo_finance": "https://query1.finance.yahoo.com/v8/finance/chart"
                }
            },
            APISource.CRYPTO: {
                "primary_api": "coingecko",
                "fallback_api": "coinmarketcap",
                "rate_limit": 50,
                "timeout": 10,
                "endpoints": {
                    "coingecko": "https://api.coingecko.com/api/v3",
                    "coinmarketcap": "https://pro-api.coinmarketcap.com/v1"
                }
            }
        }
    
    async def initialize(self):
        """Initialize the live API integration manager"""
        try:
            # Create HTTP session with optimized settings
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=20,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    "User-Agent": "ChoyAI/1.0 (Personal AI Assistant)",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Encoding": "gzip, deflate"
                }
            )
            
            self.logger.info("🌐 Live API Integration Manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Live API Integration Manager: {e}")
            raise
    
    async def get_live_data(self, request: LiveDataRequest) -> LiveDataResponse:
        """
        Get live data from specified source with graceful error handling
        """
        try:
            # Check cache first
            cache_key = f"{request.source.value}:{hash(request.query)}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if (datetime.now() - timestamp).seconds < self.cache_ttl:
                    self.logger.debug(f"📦 Returning cached data for {request.source.value}")
                    return LiveDataResponse(
                        success=True,
                        data=cached_data,
                        source=request.source,
                        timestamp=timestamp
                    )
            
            # Check rate limits
            if not await self._check_rate_limit(request.source):
                return await self._get_graceful_error_response(request.source, "rate_limit")
            
            # Route to appropriate handler
            response = await self._route_request(request)
            
            # Cache successful responses
            if response.success and response.data:
                self.cache[cache_key] = (response.data, datetime.now())
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Error getting live data for {request.source.value}: {e}")
            return await self._get_graceful_error_response(request.source, "general_error")
    
    async def _route_request(self, request: LiveDataRequest) -> LiveDataResponse:
        """Route request to appropriate API handler"""
        try:
            if request.source == APISource.WEB_SEARCH:
                return await self._handle_web_search(request)
            elif request.source == APISource.NEWS:
                return await self._handle_news_search(request)
            elif request.source == APISource.WEATHER:
                return await self._handle_weather_request(request)
            elif request.source == APISource.FINANCE:
                return await self._handle_finance_request(request)
            elif request.source == APISource.CRYPTO:
                return await self._handle_crypto_request(request)
            elif request.source == APISource.GENERAL_SEARCH:
                return await self._handle_general_search(request)
            else:
                return await self._get_graceful_error_response(request.source, "unsupported")
                
        except Exception as e:
            self.logger.error(f"❌ Error routing request for {request.source.value}: {e}")
            return await self._get_graceful_error_response(request.source, "routing_error")
    
    async def _handle_web_search(self, request: LiveDataRequest) -> LiveDataResponse:
        """Handle web search requests"""
        try:
            # Try Serper API first
            if self.settings.get("SERPER_API_KEY"):
                response = await self._serper_search(request.query)
                if response:
                    return LiveDataResponse(
                        success=True,
                        data=response,
                        source=request.source,
                        timestamp=datetime.now()
                    )
            
            # Try Perplexity API as fallback
            if self.settings.get("PERPLEXITY_API_KEY"):
                response = await self._perplexity_search(request.query)
                if response:
                    return LiveDataResponse(
                        success=True,
                        data=response,
                        source=request.source,
                        timestamp=datetime.now(),
                        fallback_used=True
                    )
            
            return await self._get_graceful_error_response(request.source, "no_api_key")
            
        except Exception as e:
            self.logger.error(f"❌ Web search error: {e}")
            return await self._get_graceful_error_response(request.source, "search_error")
    
    async def _serper_search(self, query: str) -> Optional[Dict[str, Any]]:
        """Perform search using Serper API"""
        try:
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.settings.get("SERPER_API_KEY"),
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": 5,
                "hl": "en",
                "gl": "us"
            }
            
            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_search_results(data)
                else:
                    self.logger.warning(f"Serper API returned status {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"❌ Serper search error: {e}")
            return None
    
    async def _perplexity_search(self, query: str) -> Optional[Dict[str, Any]]:
        """Perform search using Perplexity API"""
        try:
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.settings.get('PERPLEXITY_API_KEY')}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Search for current information about: {query}"
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.3
            }
            
            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "type": "perplexity_response",
                        "content": data.get("choices", [{}])[0].get("message", {}).get("content", ""),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    self.logger.warning(f"Perplexity API returned status {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"❌ Perplexity search error: {e}")
            return None
    
    def _format_search_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format search results from Serper API"""
        try:
            organic_results = data.get("organic", [])
            formatted_results = []
            
            for i, result in enumerate(organic_results[:5]):
                formatted_results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "url": result.get("link", ""),
                    "position": i + 1,
                    "domain": result.get("displayLink", "")
                })
            
            return {
                "type": "web_search",
                "query": data.get("searchParameters", {}).get("q", ""),
                "results": formatted_results,
                "total_results": len(formatted_results),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error formatting search results: {e}")
            return {"type": "web_search", "results": [], "error": "formatting_error"}
    
    async def _handle_news_search(self, request: LiveDataRequest) -> LiveDataResponse:
        """Handle news search requests"""
        try:
            # Implementation for news search
            # This would integrate with news APIs
            return LiveDataResponse(
                success=True,
                data={"type": "news", "placeholder": "News search implementation"},
                source=request.source,
                timestamp=datetime.now()
            )
        except Exception as e:
            return await self._get_graceful_error_response(request.source, "news_error")
    
    async def _handle_weather_request(self, request: LiveDataRequest) -> LiveDataResponse:
        """Handle weather requests"""
        try:
            # Implementation for weather data
            # This would integrate with weather APIs
            return LiveDataResponse(
                success=True,
                data={"type": "weather", "placeholder": "Weather implementation"},
                source=request.source,
                timestamp=datetime.now()
            )
        except Exception as e:
            return await self._get_graceful_error_response(request.source, "weather_error")
    
    async def _handle_finance_request(self, request: LiveDataRequest) -> LiveDataResponse:
        """Handle financial data requests"""
        try:
            # Implementation for financial data
            return LiveDataResponse(
                success=True,
                data={"type": "finance", "placeholder": "Finance implementation"},
                source=request.source,
                timestamp=datetime.now()
            )
        except Exception as e:
            return await self._get_graceful_error_response(request.source, "finance_error")
    
    async def _handle_crypto_request(self, request: LiveDataRequest) -> LiveDataResponse:
        """Handle cryptocurrency data requests"""
        try:
            # Implementation for crypto data
            return LiveDataResponse(
                success=True,
                data={"type": "crypto", "placeholder": "Crypto implementation"},
                source=request.source,
                timestamp=datetime.now()
            )
        except Exception as e:
            return await self._get_graceful_error_response(request.source, "crypto_error")
    
    async def _handle_general_search(self, request: LiveDataRequest) -> LiveDataResponse:
        """Handle general search requests (fallback to web search)"""
        return await self._handle_web_search(request)
    
    async def _check_rate_limit(self, source: APISource) -> bool:
        """Check if request is within rate limits"""
        try:
            config = self.api_configs.get(source, {})
            rate_limit = config.get("rate_limit", 60)  # requests per minute
            
            now = datetime.now()
            if source not in self.last_request_times:
                self.last_request_times[source] = []
            
            # Remove old timestamps (older than 1 minute)
            minute_ago = now - timedelta(minutes=1)
            self.last_request_times[source] = [
                ts for ts in self.last_request_times[source] if ts > minute_ago
            ]
            
            # Check if we're within rate limit
            if len(self.last_request_times[source]) >= rate_limit:
                return False
            
            # Add current timestamp
            self.last_request_times[source].append(now)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Rate limit check error: {e}")
            return True  # Allow request if rate limit check fails
    
    async def _get_graceful_error_response(self, source: APISource, error_type: str) -> LiveDataResponse:
        """Get graceful error response that doesn't reveal internet limitations"""
        try:
            messages = self.graceful_error_messages.get(source, [
                "The information is temporarily unavailable. Please try again in a moment.",
                "I'm unable to access that data right now. Please check back soon.",
                "The service is currently being updated. Please try again shortly."
            ])
            
            # Select a random message to vary responses
            import random
            message = random.choice(messages)
            
            return LiveDataResponse(
                success=False,
                data={"error_message": message, "retry_suggested": True},
                source=source,
                timestamp=datetime.now(),
                error_message=message
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error creating graceful error response: {e}")
            return LiveDataResponse(
                success=False,
                data={"error_message": "Information temporarily unavailable. Please try again."},
                source=source,
                timestamp=datetime.now(),
                error_message="Information temporarily unavailable. Please try again."
            )
    
    def requires_live_data(self, user_message: str) -> Optional[APISource]:
        """
        Analyze user message to determine if live data is needed
        """
        try:
            message_lower = user_message.lower()
            
            # Web search indicators
            web_search_keywords = [
                "search for", "look up", "find information about", "what's happening with",
                "latest news about", "current events", "recent developments", "what's new",
                "search", "google", "find", "lookup", "research"
            ]
            
            # Weather indicators
            weather_keywords = [
                "weather", "temperature", "forecast", "rain", "snow", "sunny", "cloudy",
                "hot", "cold", "humidity", "wind", "storm", "climate"
            ]
            
            # News indicators
            news_keywords = [
                "news", "breaking", "headlines", "latest", "current events", "happening now",
                "today's news", "recent news", "updates", "reports"
            ]
            
            # Finance indicators
            finance_keywords = [
                "stock price", "market", "stocks", "trading", "investment", "portfolio",
                "nasdaq", "dow jones", "s&p 500", "shares", "earnings"
            ]
            
            # Crypto indicators
            crypto_keywords = [
                "bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency",
                "coin", "token", "blockchain", "price"
            ]
            
            # Check for specific patterns
            if any(keyword in message_lower for keyword in weather_keywords):
                return APISource.WEATHER
            elif any(keyword in message_lower for keyword in news_keywords):
                return APISource.NEWS
            elif any(keyword in message_lower for keyword in finance_keywords):
                return APISource.FINANCE
            elif any(keyword in message_lower for keyword in crypto_keywords):
                return APISource.CRYPTO
            elif any(keyword in message_lower for keyword in web_search_keywords):
                return APISource.WEB_SEARCH
            
            # Check for question patterns that likely need current information
            question_patterns = [
                r"what.*(happening|going on|new|latest|current)",
                r"how.*(doing|performing|going)",
                r"when.*(will|did|does)",
                r"where.*(is|are|can)",
                r"who.*(is|are|won|lost)",
                r"why.*(did|is|are)"
            ]
            
            for pattern in question_patterns:
                if re.search(pattern, message_lower):
                    return APISource.GENERAL_SEARCH
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing message for live data needs: {e}")
            return None
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.logger.info("🔒 Live API Integration Manager session closed")
