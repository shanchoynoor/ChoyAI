"""
ChoyAI Productivity Module 14: Online Agent

Provides web search, live information access, and online services integration.
Uses Serper API for web search and various other APIs for live data.

Cost: FREE tier with rate limits
- Serper API: 1,000 free searches/month
- Most APIs used are free tier
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from app.modules.productivity import (
    BaseProductivityModule, ModuleRequest, ModuleResponse, ModuleType, ModuleConfig
)
from app.config.settings import get_settings
from app.core.ai_providers import AIProviderManager


class OnlineServiceType(Enum):
    """Types of online services"""
    WEB_SEARCH = "web_search"
    NEWS = "news"
    WEATHER = "weather"
    FINANCE = "finance"
    MAPS = "maps"
    TRANSLATE = "translate"
    SOCIAL_MEDIA = "social_media"
    GENERAL_INFO = "general_info"


@dataclass
class SearchResult:
    """Web search result structure"""
    title: str
    url: str
    snippet: str
    position: int
    domain: str


@dataclass
class WeatherInfo:
    """Weather information structure"""
    location: str
    temperature: float
    condition: str
    humidity: int
    wind_speed: float
    forecast: List[Dict[str, Any]]


class OnlineAgentModule(BaseProductivityModule):
    """
    Online Agent Module - Web search and live information access
    
    Capabilities:
    - Web search via Serper API
    - Weather information via WeatherAPI
    - News and current events
    - Financial data
    - Maps and location services
    - Translation services
    - Social media trends
    """
    
    def __init__(self, config: ModuleConfig, ai_provider_manager: AIProviderManager):
        super().__init__(config, ai_provider_manager)
        
        self.settings = get_settings()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API Keys from environment
        self.serper_api_key = self.settings.get("SERPER_API_KEY")
        self.weather_api_key = self.settings.get("WEATHER_API_KEY")
        self.news_api_key = self.settings.get("NEWS_API_KEY")
        self.perplexity_api_key = self.settings.get("PERPLEXITY_API_KEY")
        
        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = 1.0  # 1 second between requests
        
    async def initialize(self):
        """Initialize the online agent module"""
        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            self.logger.info("🌐 Online Agent Module initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Online Agent Module: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def get_capabilities(self) -> List[str]:
        """Get list of module capabilities"""
        return [
            "Web Search - Search the internet for current information",
            "Weather Information - Get weather forecasts and conditions",
            "News & Current Events - Access latest news and trending topics", 
            "Financial Data - Stock prices, cryptocurrency, and market information",
            "Maps & Location - Find locations, addresses, and directions",
            "Translation Services - Translate text between languages",
            "Social Media Trends - Current trending topics and social information",
            "Live Information Access - Real-time data from various sources"
        ]
    
    def get_supported_actions(self) -> List[str]:
        """Get list of supported actions"""
        return [
            "web_search", "search_web", "search",
            "get_weather", "weather", "forecast",
            "get_news", "news", "current_events",
            "get_finance", "stock_price", "crypto_price",
            "get_maps", "find_location", "directions",
            "translate", "translate_text",
            "get_trends", "social_trends",
            "general_search", "live_info"
        ]
    
    async def process_request(self, request: ModuleRequest) -> ModuleResponse:
        """Process online agent request"""
        try:
            # Rate limiting
            await self._enforce_rate_limit(request.user_id)
            
            action = request.action.lower()
            
            # Route to appropriate handler
            if action in ["web_search", "search_web", "search", "general_search"]:
                return await self._web_search(request)
            elif action in ["get_weather", "weather", "forecast"]:
                return await self._get_weather(request)
            elif action in ["get_news", "news", "current_events"]:
                return await self._get_news(request)
            elif action in ["get_finance", "stock_price", "crypto_price"]:
                return await self._get_finance(request)
            elif action in ["get_maps", "find_location", "directions"]:
                return await self._get_maps(request)
            elif action in ["translate", "translate_text"]:
                return await self._translate(request)
            elif action in ["get_trends", "social_trends"]:
                return await self._get_trends(request)
            elif action in ["live_info"]:
                return await self._get_live_info(request)
            else:
                return ModuleResponse(
                    success=False,
                    message=f"Unknown action: {action}",
                    error=f"Action '{action}' not supported"
                )
                
        except Exception as e:
            self.logger.error(f"❌ Error processing online agent request: {e}")
            return ModuleResponse(
                success=False,
                message="Failed to process online request",
                error=str(e)
            )
    
    async def _enforce_rate_limit(self, user_id: str):
        """Enforce rate limiting per user"""
        now = datetime.now()
        if user_id in self.last_request_time:
            time_diff = (now - self.last_request_time[user_id]).total_seconds()
            if time_diff < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - time_diff)
        
        self.last_request_time[user_id] = now
    
    async def _web_search(self, request: ModuleRequest) -> ModuleResponse:
        """Perform web search using Serper API"""
        try:
            query = request.data.get("query") or request.data.get("q")
            if not query:
                return ModuleResponse(
                    success=False,
                    message="Search query is required",
                    error="Missing 'query' parameter"
                )
            
            if not self.serper_api_key:
                return ModuleResponse(
                    success=False,
                    message="Web search is not configured",
                    error="SERPER_API_KEY not set"
                )
            
            # Call Serper API
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": request.data.get("num_results", 5),
                "gl": request.data.get("country", "us"),
                "hl": request.data.get("language", "en")
            }
            
            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse results
                    results = []
                    organic = data.get("organic", [])
                    
                    for i, result in enumerate(organic[:10]):  # Limit to 10 results
                        search_result = SearchResult(
                            title=result.get("title", ""),
                            url=result.get("link", ""),
                            snippet=result.get("snippet", ""),
                            position=i + 1,
                            domain=result.get("domain", "")
                        )
                        results.append(search_result.__dict__)
                    
                    # Include answer box if available
                    answer_box = data.get("answerBox")
                    knowledge_graph = data.get("knowledgeGraph")
                    
                    response_data = {
                        "query": query,
                        "results": results,
                        "total_results": len(results),
                        "answer_box": answer_box,
                        "knowledge_graph": knowledge_graph,
                        "search_timestamp": datetime.now().isoformat()
                    }
                    
                    return ModuleResponse(
                        success=True,
                        data=response_data,
                        message=f"Found {len(results)} search results for '{query}'",
                        cost_estimate=0.001,
                        external_apis_used=["Serper API"]
                    )
                else:
                    error_text = await response.text()
                    return ModuleResponse(
                        success=False,
                        message=f"Search failed with status {response.status}",
                        error=error_text
                    )
                    
        except Exception as e:
            self.logger.error(f"❌ Web search error: {e}")
            return ModuleResponse(
                success=False,
                message="Web search failed",
                error=str(e)
            )
    
    async def _get_weather(self, request: ModuleRequest) -> ModuleResponse:
        """Get weather information"""
        try:
            location = request.data.get("location")
            if not location:
                return ModuleResponse(
                    success=False,
                    message="Location is required for weather information",
                    error="Missing 'location' parameter"
                )
            
            if not self.weather_api_key:
                return ModuleResponse(
                    success=False,
                    message="Weather service is not configured",
                    error="WEATHER_API_KEY not set"
                )
            
            # Call WeatherAPI
            url = f"http://api.weatherapi.com/v1/forecast.json"
            params = {
                "key": self.weather_api_key,
                "q": location,
                "days": request.data.get("days", 3),
                "aqi": "yes",
                "alerts": "yes"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    current = data.get("current", {})
                    forecast = data.get("forecast", {}).get("forecastday", [])
                    location_info = data.get("location", {})
                    
                    weather_info = {
                        "location": f"{location_info.get('name')}, {location_info.get('country')}",
                        "current": {
                            "temperature_c": current.get("temp_c"),
                            "temperature_f": current.get("temp_f"),
                            "condition": current.get("condition", {}).get("text"),
                            "humidity": current.get("humidity"),
                            "wind_speed_kph": current.get("wind_kph"),
                            "wind_speed_mph": current.get("wind_mph"),
                            "feels_like_c": current.get("feelslike_c"),
                            "feels_like_f": current.get("feelslike_f"),
                            "uv_index": current.get("uv"),
                            "visibility_km": current.get("vis_km"),
                            "visibility_miles": current.get("vis_miles")
                        },
                        "forecast": [
                            {
                                "date": day.get("date"),
                                "max_temp_c": day.get("day", {}).get("maxtemp_c"),
                                "max_temp_f": day.get("day", {}).get("maxtemp_f"),
                                "min_temp_c": day.get("day", {}).get("mintemp_c"),
                                "min_temp_f": day.get("day", {}).get("mintemp_f"),
                                "condition": day.get("day", {}).get("condition", {}).get("text"),
                                "chance_of_rain": day.get("day", {}).get("daily_chance_of_rain"),
                                "chance_of_snow": day.get("day", {}).get("daily_chance_of_snow")
                            }
                            for day in forecast
                        ],
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    return ModuleResponse(
                        success=True,
                        data=weather_info,
                        message=f"Weather information for {location}",
                        cost_estimate=0.0,  # WeatherAPI is free
                        external_apis_used=["WeatherAPI"]
                    )
                else:
                    error_text = await response.text()
                    return ModuleResponse(
                        success=False,
                        message=f"Weather request failed with status {response.status}",
                        error=error_text
                    )
                    
        except Exception as e:
            self.logger.error(f"❌ Weather error: {e}")
            return ModuleResponse(
                success=False,
                message="Weather request failed",
                error=str(e)
            )
    
    async def _get_news(self, request: ModuleRequest) -> ModuleResponse:
        """Get current news"""
        try:
            query = request.data.get("query", "latest news")
            category = request.data.get("category", "general")
            
            # Try web search for news if no dedicated news API
            news_query = f"{query} news latest"
            
            # Use web search to get current news
            search_request = ModuleRequest(
                user_id=request.user_id,
                module_type=ModuleType.ONLINE_AGENT,
                action="web_search",
                data={
                    "query": news_query,
                    "num_results": 8
                }
            )
            
            search_response = await self._web_search(search_request)
            
            if search_response.success:
                # Filter and format as news
                results = search_response.data.get("results", [])
                news_results = []
                
                for result in results:
                    # Check if it looks like a news article
                    domain = result.get("domain", "").lower()
                    title = result.get("title", "").lower()
                    
                    is_news = any(news_indicator in domain for news_indicator in [
                        "news", "bbc", "cnn", "reuters", "ap", "guardian", 
                        "times", "post", "herald", "journal", "telegraph",
                        "bloomberg", "forbes", "techcrunch"
                    ]) or any(news_word in title for news_word in [
                        "breaking", "latest", "update", "report", "announced"
                    ])
                    
                    if is_news:
                        news_results.append({
                            "headline": result.get("title"),
                            "summary": result.get("snippet"),
                            "url": result.get("url"),
                            "source": result.get("domain"),
                            "position": result.get("position")
                        })
                
                news_data = {
                    "query": query,
                    "category": category,
                    "articles": news_results[:6],  # Limit to 6 articles
                    "total_found": len(news_results),
                    "timestamp": datetime.now().isoformat()
                }
                
                return ModuleResponse(
                    success=True,
                    data=news_data,
                    message=f"Found {len(news_results)} news articles",
                    cost_estimate=0.001,
                    external_apis_used=["Serper API"]
                )
            else:
                return search_response
                
        except Exception as e:
            self.logger.error(f"❌ News error: {e}")
            return ModuleResponse(
                success=False,
                message="News request failed",
                error=str(e)
            )
    
    async def _get_finance(self, request: ModuleRequest) -> ModuleResponse:
        """Get financial information"""
        try:
            symbol = request.data.get("symbol")
            if not symbol:
                return ModuleResponse(
                    success=False,
                    message="Symbol is required for financial data",
                    error="Missing 'symbol' parameter"
                )
            
            # Use web search for financial data
            finance_query = f"{symbol} stock price current market data"
            
            search_request = ModuleRequest(
                user_id=request.user_id,
                module_type=ModuleType.ONLINE_AGENT,
                action="web_search",
                data={
                    "query": finance_query,
                    "num_results": 3
                }
            )
            
            search_response = await self._web_search(search_request)
            
            if search_response.success:
                results = search_response.data
                
                # Look for answer box with financial data
                answer_box = results.get("answer_box")
                knowledge_graph = results.get("knowledge_graph")
                
                finance_data = {
                    "symbol": symbol.upper(),
                    "search_results": results.get("results", [])[:3],
                    "answer_box": answer_box,
                    "knowledge_graph": knowledge_graph,
                    "timestamp": datetime.now().isoformat()
                }
                
                return ModuleResponse(
                    success=True,
                    data=finance_data,
                    message=f"Financial information for {symbol.upper()}",
                    cost_estimate=0.001,
                    external_apis_used=["Serper API"]
                )
            else:
                return search_response
                
        except Exception as e:
            self.logger.error(f"❌ Finance error: {e}")
            return ModuleResponse(
                success=False,
                message="Finance request failed",
                error=str(e)
            )
    
    async def _get_maps(self, request: ModuleRequest) -> ModuleResponse:
        """Get maps and location information"""
        try:
            location = request.data.get("location")
            if not location:
                return ModuleResponse(
                    success=False,
                    message="Location is required",
                    error="Missing 'location' parameter"
                )
            
            # Use web search for location information
            maps_query = f"{location} address location map directions"
            
            search_request = ModuleRequest(
                user_id=request.user_id,
                module_type=ModuleType.ONLINE_AGENT,
                action="web_search",
                data={
                    "query": maps_query,
                    "num_results": 3
                }
            )
            
            search_response = await self._web_search(search_request)
            
            if search_response.success:
                results = search_response.data
                
                maps_data = {
                    "location": location,
                    "search_results": results.get("results", [])[:3],
                    "knowledge_graph": results.get("knowledge_graph"),
                    "timestamp": datetime.now().isoformat()
                }
                
                return ModuleResponse(
                    success=True,
                    data=maps_data,
                    message=f"Location information for {location}",
                    cost_estimate=0.001,
                    external_apis_used=["Serper API"]
                )
            else:
                return search_response
                
        except Exception as e:
            self.logger.error(f"❌ Maps error: {e}")
            return ModuleResponse(
                success=False,
                message="Maps request failed",
                error=str(e)
            )
    
    async def _translate(self, request: ModuleRequest) -> ModuleResponse:
        """Translate text using web search"""
        try:
            text = request.data.get("text")
            target_language = request.data.get("target_language", "English")
            
            if not text:
                return ModuleResponse(
                    success=False,
                    message="Text is required for translation",
                    error="Missing 'text' parameter"
                )
            
            # Use web search for translation
            translate_query = f"translate '{text}' to {target_language}"
            
            search_request = ModuleRequest(
                user_id=request.user_id,
                module_type=ModuleType.ONLINE_AGENT,
                action="web_search",
                data={
                    "query": translate_query,
                    "num_results": 2
                }
            )
            
            search_response = await self._web_search(search_request)
            
            if search_response.success:
                results = search_response.data
                
                translate_data = {
                    "original_text": text,
                    "target_language": target_language,
                    "search_results": results.get("results", [])[:2],
                    "answer_box": results.get("answer_box"),
                    "timestamp": datetime.now().isoformat()
                }
                
                return ModuleResponse(
                    success=True,
                    data=translate_data,
                    message=f"Translation results for text to {target_language}",
                    cost_estimate=0.001,
                    external_apis_used=["Serper API"]
                )
            else:
                return search_response
                
        except Exception as e:
            self.logger.error(f"❌ Translation error: {e}")
            return ModuleResponse(
                success=False,
                message="Translation request failed",
                error=str(e)
            )
    
    async def _get_trends(self, request: ModuleRequest) -> ModuleResponse:
        """Get current trends"""
        try:
            category = request.data.get("category", "general")
            
            # Use web search for current trends
            trends_query = f"trending {category} latest trends 2025"
            
            search_request = ModuleRequest(
                user_id=request.user_id,
                module_type=ModuleType.ONLINE_AGENT,
                action="web_search",
                data={
                    "query": trends_query,
                    "num_results": 5
                }
            )
            
            search_response = await self._web_search(search_request)
            
            if search_response.success:
                results = search_response.data
                
                trends_data = {
                    "category": category,
                    "search_results": results.get("results", [])[:5],
                    "knowledge_graph": results.get("knowledge_graph"),
                    "timestamp": datetime.now().isoformat()
                }
                
                return ModuleResponse(
                    success=True,
                    data=trends_data,
                    message=f"Current trends in {category}",
                    cost_estimate=0.001,
                    external_apis_used=["Serper API"]
                )
            else:
                return search_response
                
        except Exception as e:
            self.logger.error(f"❌ Trends error: {e}")
            return ModuleResponse(
                success=False,
                message="Trends request failed",
                error=str(e)
            )
    
    async def _get_live_info(self, request: ModuleRequest) -> ModuleResponse:
        """Get general live information"""
        try:
            query = request.data.get("query", "current information")
            info_type = request.data.get("type", "general")
            
            # Enhanced query for better results
            live_query = f"{query} latest current 2025 live information"
            
            search_request = ModuleRequest(
                user_id=request.user_id,
                module_type=ModuleType.ONLINE_AGENT,
                action="web_search",
                data={
                    "query": live_query,
                    "num_results": 6
                }
            )
            
            search_response = await self._web_search(search_request)
            
            if search_response.success:
                results = search_response.data
                
                live_data = {
                    "query": query,
                    "type": info_type,
                    "search_results": results.get("results", [])[:6],
                    "answer_box": results.get("answer_box"),
                    "knowledge_graph": results.get("knowledge_graph"),
                    "timestamp": datetime.now().isoformat()
                }
                
                return ModuleResponse(
                    success=True,
                    data=live_data,
                    message=f"Live information for '{query}'",
                    cost_estimate=0.001,
                    external_apis_used=["Serper API"]
                )
            else:
                return search_response
                
        except Exception as e:
            self.logger.error(f"❌ Live info error: {e}")
            return ModuleResponse(
                success=False,
                message="Live information request failed",
                error=str(e)
            )


# Export
__all__ = ["OnlineAgentModule", "OnlineServiceType", "SearchResult", "WeatherInfo"]
