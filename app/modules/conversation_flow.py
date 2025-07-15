"""
Enhanced Conversation Flow with LangGraph Integration

Implements state machine-based conversation flows for complex interactions
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, TypedDict, Annotated
from datetime import datetime
from enum import Enum

try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
    from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # Fallback types for when LangGraph is not available
    class StateGraph:
        def __init__(self): pass
    END = "END"

from app.config.settings import settings


class ConversationState(Enum):
    """Conversation flow states"""
    GREETING = "greeting"
    GENERAL_CHAT = "general_chat"
    TASK_ASSISTANCE = "task_assistance"
    PROBLEM_SOLVING = "problem_solving"
    PERSONA_SWITCHING = "persona_switching"
    MEMORY_RECALL = "memory_recall"
    KNOWLEDGE_QUERY = "knowledge_query"
    EMOTIONAL_SUPPORT = "emotional_support"
    CONCLUSION = "conclusion"


class GraphState(TypedDict):
    """State for LangGraph conversation flow"""
    messages: Annotated[List[BaseMessage], add_messages] if LANGGRAPH_AVAILABLE else List[Any]
    user_id: str
    current_persona: str
    conversation_context: Dict[str, Any]
    flow_state: str
    user_intent: str
    extracted_entities: Dict[str, Any]
    response_history: List[str]
    metadata: Dict[str, Any]


class ConversationFlowManager:
    """Manages complex conversation flows using LangGraph state machines"""
    
    def __init__(self, ai_engine=None, rag_engine=None):
        self.logger = logging.getLogger(__name__)
        self.ai_engine = ai_engine
        self.rag_engine = rag_engine
        self.graph = None
        self.compiled_graph = None
        
        # Intent classification patterns
        self.intent_patterns = {
            "greeting": ["hello", "hi", "hey", "good morning", "good evening"],
            "task_assistance": ["help me", "can you", "how do i", "need help", "assist"],
            "problem_solving": ["problem", "issue", "error", "bug", "fix", "solve"],
            "persona_switching": ["switch to", "change persona", "be like", "act as"],
            "memory_recall": ["remember", "what did", "recall", "you said", "we talked"],
            "knowledge_query": ["what is", "explain", "define", "tell me about", "information"],
            "emotional_support": ["feeling", "sad", "happy", "frustrated", "support", "comfort"]
        }
        
        if not LANGGRAPH_AVAILABLE:
            self.logger.warning("LangGraph not available. Using simplified conversation flow")
    
    async def initialize(self):
        """Initialize the conversation flow graph"""
        try:
            self.logger.info("🔄 Initializing Conversation Flow Manager...")
            
            if LANGGRAPH_AVAILABLE:
                await self._build_conversation_graph()
                self.logger.info("✅ LangGraph conversation flow initialized")
            else:
                self.logger.info("✅ Fallback conversation flow initialized")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize conversation flow: {e}")
            return False
    
    async def _build_conversation_graph(self):
        """Build the LangGraph conversation state machine"""
        if not LANGGRAPH_AVAILABLE:
            return
        
        # Create the state graph
        workflow = StateGraph(GraphState)
        
        # Add nodes for each conversation state
        workflow.add_node("intent_classifier", self._classify_intent)
        workflow.add_node("greeting_handler", self._handle_greeting)
        workflow.add_node("general_chat_handler", self._handle_general_chat)
        workflow.add_node("task_assistance_handler", self._handle_task_assistance)
        workflow.add_node("problem_solving_handler", self._handle_problem_solving)
        workflow.add_node("persona_switching_handler", self._handle_persona_switching)
        workflow.add_node("memory_recall_handler", self._handle_memory_recall)
        workflow.add_node("knowledge_query_handler", self._handle_knowledge_query)
        workflow.add_node("emotional_support_handler", self._handle_emotional_support)
        workflow.add_node("response_generator", self._generate_response)
        
        # Set entry point
        workflow.set_entry_point("intent_classifier")
        
        # Add conditional edges based on intent classification
        workflow.add_conditional_edges(
            "intent_classifier",
            self._route_by_intent,
            {
                "greeting": "greeting_handler",
                "general_chat": "general_chat_handler",
                "task_assistance": "task_assistance_handler",
                "problem_solving": "problem_solving_handler",
                "persona_switching": "persona_switching_handler",
                "memory_recall": "memory_recall_handler",
                "knowledge_query": "knowledge_query_handler",
                "emotional_support": "emotional_support_handler"
            }
        )
        
        # All handlers lead to response generation
        for handler in ["greeting_handler", "general_chat_handler", "task_assistance_handler",
                       "problem_solving_handler", "persona_switching_handler", "memory_recall_handler",
                       "knowledge_query_handler", "emotional_support_handler"]:
            workflow.add_edge(handler, "response_generator")
        
        # Response generator ends the flow
        workflow.add_edge("response_generator", END)
        
        # Compile the graph
        self.compiled_graph = workflow.compile()
        self.logger.info("📊 LangGraph conversation flow compiled")
    
    async def process_conversation(
        self,
        user_id: str,
        message: str,
        conversation_context: Dict[str, Any],
        persona: str = "choy"
    ) -> Tuple[str, Dict[str, Any]]:
        """Process a conversation through the state machine"""
        try:
            if LANGGRAPH_AVAILABLE and self.compiled_graph:
                return await self._process_with_langgraph(user_id, message, conversation_context, persona)
            else:
                return await self._process_with_fallback(user_id, message, conversation_context, persona)
                
        except Exception as e:
            self.logger.error(f"❌ Error processing conversation: {e}")
            return "I apologize, but I encountered an error processing your message.", {"error": str(e)}
    
    async def _process_with_langgraph(
        self,
        user_id: str,
        message: str,
        conversation_context: Dict[str, Any],
        persona: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Process conversation using LangGraph"""
        
        # Prepare initial state
        initial_state = GraphState(
            messages=[HumanMessage(content=message)],
            user_id=user_id,
            current_persona=persona,
            conversation_context=conversation_context,
            flow_state="initial",
            user_intent="unknown",
            extracted_entities={},
            response_history=[],
            metadata={"timestamp": datetime.now().isoformat()}
        )
        
        # Run the graph
        result = await self.compiled_graph.ainvoke(initial_state)
        
        # Extract response and metadata
        response = result.get("generated_response", "I'm here to help!")
        flow_metadata = {
            "intent": result.get("user_intent", "unknown"),
            "flow_state": result.get("flow_state", "completed"),
            "entities": result.get("extracted_entities", {}),
            "persona_used": result.get("current_persona", persona)
        }
        
        return response, flow_metadata
    
    async def _process_with_fallback(
        self,
        user_id: str,
        message: str,
        conversation_context: Dict[str, Any],
        persona: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Fallback processing without LangGraph"""
        
        # Simple intent classification
        intent = self._classify_intent_simple(message)
        
        # Route to appropriate handler
        if intent == "greeting":
            response = await self._handle_greeting_simple(message, conversation_context, persona)
        elif intent == "task_assistance":
            response = await self._handle_task_assistance_simple(message, conversation_context, persona)
        elif intent == "knowledge_query":
            response = await self._handle_knowledge_query_simple(message, conversation_context, persona)
        else:
            response = await self._handle_general_chat_simple(message, conversation_context, persona)
        
        metadata = {
            "intent": intent,
            "flow_state": "completed",
            "fallback_mode": True,
            "persona_used": persona
        }
        
        return response, metadata
    
    # LangGraph Node Functions
    
    async def _classify_intent(self, state: GraphState) -> GraphState:
        """Classify user intent from the message"""
        if not state["messages"]:
            state["user_intent"] = "general_chat"
            return state
        
        message = state["messages"][-1].content.lower()
        
        # Score each intent
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in message)
            if score > 0:
                intent_scores[intent] = score
        
        # Determine best intent
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            state["user_intent"] = best_intent
        else:
            state["user_intent"] = "general_chat"
        
        state["flow_state"] = "intent_classified"
        return state
    
    def _route_by_intent(self, state: GraphState) -> str:
        """Route to appropriate handler based on intent"""
        return state["user_intent"]
    
    async def _handle_greeting(self, state: GraphState) -> GraphState:
        """Handle greeting interactions"""
        state["flow_state"] = "greeting_processed"
        state["conversation_context"]["greeting_handled"] = True
        
        # Extract time-based greeting
        current_hour = datetime.now().hour
        if current_hour < 12:
            state["extracted_entities"]["time_of_day"] = "morning"
        elif current_hour < 17:
            state["extracted_entities"]["time_of_day"] = "afternoon"
        else:
            state["extracted_entities"]["time_of_day"] = "evening"
        
        return state
    
    async def _handle_general_chat(self, state: GraphState) -> GraphState:
        """Handle general conversation"""
        state["flow_state"] = "general_chat_processed"
        return state
    
    async def _handle_task_assistance(self, state: GraphState) -> GraphState:
        """Handle task assistance requests"""
        state["flow_state"] = "task_assistance_processed"
        
        # Extract task-related entities
        message = state["messages"][-1].content.lower()
        if "code" in message or "programming" in message:
            state["extracted_entities"]["task_type"] = "programming"
        elif "write" in message or "document" in message:
            state["extracted_entities"]["task_type"] = "writing"
        else:
            state["extracted_entities"]["task_type"] = "general"
        
        return state
    
    async def _handle_problem_solving(self, state: GraphState) -> GraphState:
        """Handle problem-solving scenarios"""
        state["flow_state"] = "problem_solving_processed"
        state["extracted_entities"]["problem_context"] = "technical"
        return state
    
    async def _handle_persona_switching(self, state: GraphState) -> GraphState:
        """Handle persona switching requests"""
        message = state["messages"][-1].content.lower()
        
        # Extract requested persona
        if "choy" in message:
            state["current_persona"] = "choy"
        elif "rose" in message:
            state["current_persona"] = "rose"
        elif "tony" in message:
            state["current_persona"] = "tony"
        
        state["flow_state"] = "persona_switched"
        return state
    
    async def _handle_memory_recall(self, state: GraphState) -> GraphState:
        """Handle memory recall requests"""
        state["flow_state"] = "memory_recalled"
        
        # Use RAG engine for enhanced memory retrieval if available
        if self.rag_engine:
            try:
                message = state["messages"][-1].content
                memories = await self.rag_engine.retrieve_context(
                    query=message,
                    user_id=state["user_id"],
                    context_types=["conversation_rag", "user_memory"]
                )
                state["extracted_entities"]["recalled_memories"] = memories
            except Exception as e:
                self.logger.warning(f"Memory recall failed: {e}")
        
        return state
    
    async def _handle_knowledge_query(self, state: GraphState) -> GraphState:
        """Handle knowledge queries"""
        state["flow_state"] = "knowledge_queried"
        
        # Use RAG engine for knowledge retrieval if available
        if self.rag_engine:
            try:
                message = state["messages"][-1].content
                knowledge = await self.rag_engine.retrieve_context(
                    query=message,
                    user_id="global",  # Global knowledge
                    context_types=["knowledge", "core_facts"]
                )
                state["extracted_entities"]["retrieved_knowledge"] = knowledge
            except Exception as e:
                self.logger.warning(f"Knowledge query failed: {e}")
        
        return state
    
    async def _handle_emotional_support(self, state: GraphState) -> GraphState:
        """Handle emotional support scenarios"""
        state["flow_state"] = "emotional_support_provided"
        state["extracted_entities"]["emotional_context"] = "support_needed"
        return state
    
    async def _generate_response(self, state: GraphState) -> GraphState:
        """Generate the final response using AI engine"""
        try:
            if self.ai_engine:
                # Use the AI engine to generate response with enhanced context
                message = state["messages"][-1].content
                
                # Build enhanced context from state
                enhanced_context = {
                    "intent": state["user_intent"],
                    "flow_state": state["flow_state"],
                    "entities": state["extracted_entities"],
                    "persona": state["current_persona"],
                    "conversation_context": state["conversation_context"]
                }
                
                response = await self.ai_engine.process_message(
                    user_id=state["user_id"],
                    message=message,
                    platform="graph_flow",
                    persona=state["current_persona"],
                    context=enhanced_context
                )
                
                state["generated_response"] = response
            else:
                # Fallback response generation
                state["generated_response"] = self._generate_fallback_response(state)
            
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            state["generated_response"] = "I apologize, but I'm having trouble generating a response right now."
        
        return state
    
    # Simplified handlers for fallback mode
    
    def _classify_intent_simple(self, message: str) -> str:
        """Simple intent classification without LangGraph"""
        message_lower = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return intent
        
        return "general_chat"
    
    async def _handle_greeting_simple(self, message: str, context: Dict[str, Any], persona: str) -> str:
        """Simple greeting handler"""
        current_hour = datetime.now().hour
        if current_hour < 12:
            time_greeting = "Good morning"
        elif current_hour < 17:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"
        
        return f"{time_greeting}! I'm {persona.title()}, how can I help you today?"
    
    async def _handle_task_assistance_simple(self, message: str, context: Dict[str, Any], persona: str) -> str:
        """Simple task assistance handler"""
        return "I'd be happy to help you with that task! Could you provide more details about what you need assistance with?"
    
    async def _handle_knowledge_query_simple(self, message: str, context: Dict[str, Any], persona: str) -> str:
        """Simple knowledge query handler"""
        return "That's an interesting question! Let me share what I know about that topic."
    
    async def _handle_general_chat_simple(self, message: str, context: Dict[str, Any], persona: str) -> str:
        """Simple general chat handler"""
        return "I'm here and ready to chat! What's on your mind?"
    
    def _generate_fallback_response(self, state: GraphState) -> str:
        """Generate a fallback response when AI engine is not available"""
        intent = state.get("user_intent", "general_chat")
        persona = state.get("current_persona", "choy")
        
        responses = {
            "greeting": f"Hello! I'm {persona.title()}, nice to meet you!",
            "task_assistance": "I'm here to help with any tasks you need assistance with!",
            "problem_solving": "Let's work together to solve this problem step by step.",
            "knowledge_query": "That's a great question! Let me share what I know.",
            "emotional_support": "I'm here to listen and support you.",
            "general_chat": "I'm enjoying our conversation! What would you like to talk about?"
        }
        
        return responses.get(intent, "I'm here to help however I can!")
    
    async def get_flow_stats(self) -> Dict[str, Any]:
        """Get conversation flow statistics"""
        return {
            "langgraph_available": LANGGRAPH_AVAILABLE,
            "graph_compiled": self.compiled_graph is not None,
            "supported_intents": list(self.intent_patterns.keys()),
            "ai_engine_connected": self.ai_engine is not None,
            "rag_engine_connected": self.rag_engine is not None
        }


# Export the main class
__all__ = ["ConversationFlowManager", "ConversationState", "GraphState"]
