"""
Chat-based Orchestrator using LangGraph

This module implements a chat-based system that routes user prompts to appropriate agents:
1. Video Crawling Agent - For crawling videos with hashtags
2. Q&A Agent - For answering questions from knowledge graph

The orchestrator uses LangGraph to manage the conversation flow and agent routing.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver

from ..kg_constructor.config import get_openai_llm
from .system_prompts import CLASSIFIER_PROMPT
from .messages import (
    ConversationState, 
    AgentResponse, 
    MessageFormatter, 
    SessionManager,
    MessageValidator,
    IntentTypes,
    TaskTypes
)

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Classifies user intents to route to appropriate agents
    """
    
    def __init__(self, llm=None):
        self.llm = llm or get_openai_llm(model="gpt-4o-mini")
    
    def classify_intent(self, user_message: str) -> Dict[str, Any]:
        """
        Classify user intent and extract relevant information
        
        Args:
            user_message: The user's input message
            
        Returns:
            Dict containing intent, confidence, and extracted info
        """
        try:
            messages = [
                SystemMessage(content=CLASSIFIER_PROMPT),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            
            # Clean and parse the JSON response
            response_text = response.content.strip()
            
            # Try to find JSON in the response if it's embedded in text
            if not response_text.startswith("{"):
                import re
                json_match = re.search(r'\{[^}]*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
            
            result = json.loads(response_text)
            
            # Normalize intent to uppercase for consistent routing
            if "intent" in result:
                result["intent"] = result["intent"].upper()
            
            logger.info(f"Classified intent: {result.get('intent')} (confidence: {result.get('confidence', 0)})") 
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Intent classification JSON parse error: {e}. Response was: {response.content[:200]}")
            return {
                "intent": "GENERAL_CHAT",
                "confidence": 0.1,
                "extracted_info": {},
                "reasoning": "Failed to parse classification result"
            }
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return {
                "intent": "GENERAL_CHAT", 
                "confidence": 0.1,
                "extracted_info": {},
                "reasoning": "Classification error occurred"
            }


class VideoCrawlingAgent:
    """
    Placeholder agent for video crawling functionality
    TODO: Implement actual video crawling with hashtags
    """
    
    def __init__(self, llm=None):
        self.llm = llm or get_openai_llm(model="gpt-4o-mini")
        
    def process_crawling_request(self, user_message: str, extracted_info: Dict[str, Any], user_id: str) -> AgentResponse:
        """
        Process video crawling request (placeholder implementation)
        
        Args:
            user_message: Original user message
            extracted_info: Extracted hashtags, topics, etc.
            user_id: User identifier for personalized crawling
            
        Returns:
            AgentResponse with crawling results
        """
        try:
            hashtags = extracted_info.get('hashtags', [])
            topics = extracted_info.get('topics', [])
            
            # Placeholder implementation
            logger.info(f"Video crawling request: hashtags={hashtags}, topics={topics}")
            
            # TODO: Implement actual crawling logic here
            # - Connect to social media APIs (TikTok, YouTube, Instagram)
            # - Search for videos with specified hashtags
            # - Download/process videos
            # - Extract content using video_pipeline.py
            # - Store in knowledge graph
            
            return MessageFormatter.format_video_crawling_response(hashtags, topics)
            
        except Exception as e:
            logger.error(f"Video crawling failed: {e}")
            return MessageFormatter.format_error_response(
                message=f"Sorry, I encountered an error while setting up video crawling: {e}",
                error=str(e)
            )


class KnowledgeQAAgent:
    """
    Placeholder agent for Q&A on knowledge graph
    TODO: Implement actual knowledge graph querying and Q&A
    """
    
    def __init__(self, llm=None, neo4j_client=None):
        self.llm = llm or get_openai_llm(model="gpt-4o-mini")
        self.neo4j_client = neo4j_client  # Will be injected when available
        
    def process_qa_request(self, user_message: str, extracted_info: Dict[str, Any], user_id: str) -> AgentResponse:
        """
        Process Q&A request against knowledge graph (placeholder implementation)
        
        Args:
            user_message: Original user message  
            extracted_info: Extracted topics, questions, etc.
            user_id: User identifier for personalized knowledge
            
        Returns:
            AgentResponse with Q&A results
        """
        try:
            question = extracted_info.get('question', user_message)
            topics = extracted_info.get('topics', [])
            
            logger.info(f"Knowledge Q&A request from user {user_id}: {question}")
            
            # TODO: Implement actual knowledge graph querying
            # - Query Neo4j for relevant entities and relationships
            # - Find videos related to the question topics
            # - Retrieve transcripts and summaries
            # - Use RAG (Retrieval-Augmented Generation) to answer
            # - Cite specific videos as sources
            
            return MessageFormatter.format_knowledge_qa_response(question, user_id)
            
        except Exception as e:
            logger.error(f"Knowledge Q&A failed: {e}")
            return MessageFormatter.format_error_response(
                message=f"Sorry, I couldn't find an answer to your question: {e}",
                error=str(e)
            )


class GeneralChatAgent:
    """
    Handles general conversation and system capability explanations
    """
    
    def __init__(self, llm=None):
        self.llm = llm or get_openai_llm(model="gpt-4o-mini")
    
    def process_general_chat(self, user_message: str, context: Dict[str, Any]) -> AgentResponse:
        """
        Handle general chat and system information
        
        Args:
            user_message: User's message
            context: Conversation context
            
        Returns:
            AgentResponse with chat response
        """
        try:
            # Simple rule-based responses for common patterns
            message_lower = user_message.lower()
            
            if any(greeting in message_lower for greeting in ['hello', 'hi', 'xin chào', 'chào']):
                return MessageFormatter.format_greeting_response()
                
            elif any(capability in message_lower for capability in ['what can', 'help', 'do', 'làm gì', 'giúp']):
                return MessageFormatter.format_capabilities_response()
                
            else:
                # Generic helpful response
                return MessageFormatter.format_generic_help_response()
            
        except Exception as e:
            logger.error(f"General chat failed: {e}")
            return AgentResponse(
                success=False,
                message="I'm having trouble right now. Please try again!",
                error=str(e)
            )


class ChatOrchestrator:
    """
    Main orchestrator that manages the conversation flow using LangGraph
    """
    
    def __init__(self, llm=None, neo4j_client=None, user=None):
        self.llm = llm or get_openai_llm(model="gpt-4o-mini")
        self.user = user  # Store Django user for database operations
        
        # Initialize agents
        self.intent_classifier = IntentClassifier(llm=self.llm)
        self.video_agent = VideoCrawlingAgent(llm=self.llm)
        self.qa_agent = KnowledgeQAAgent(llm=self.llm, neo4j_client=neo4j_client)
        self.chat_agent = GeneralChatAgent(llm=self.llm)
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
        
        logger.info("ChatOrchestrator initialized with all agents")
    
    def _build_workflow(self) -> CompiledStateGraph:
        """
        Build the LangGraph workflow for conversation routing
        """
        # Create the state graph
        workflow = StateGraph(ConversationState)
        
        # Add nodes (agents)
        workflow.add_node("classify_intent", self._classify_intent_node)
        workflow.add_node("video_crawling", self._video_crawling_node)
        workflow.add_node("knowledge_qa", self._knowledge_qa_node)
        workflow.add_node("general_chat", self._general_chat_node)
        
        # Add edges (routing logic)
        workflow.set_entry_point("classify_intent")
        
        # Route based on intent classification
        workflow.add_conditional_edges(
            "classify_intent",
            self._route_by_intent,
            {
                "VIDEO_CRAWLING": "video_crawling",
                "KNOWLEDGE_QA": "knowledge_qa", 
                "GENERAL_CHAT": "general_chat",
                # Add fallback mappings for case variations
                "video_crawling": "video_crawling",
                "knowledge_qa": "knowledge_qa",
                "general_chat": "general_chat"
            }
        )
        
        # All agents end the conversation (for now)
        workflow.add_edge("video_crawling", "__end__")
        workflow.add_edge("knowledge_qa", "__end__")
        workflow.add_edge("general_chat", "__end__")
        
        # Compile with memory for session management
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    def _classify_intent_node(self, state):
        """Node for intent classification"""
        # Convert dict to ConversationState if needed
        if isinstance(state, dict):
            state = ConversationState(**state)
        
        last_message = state.messages[-1]["content"] if state.messages else ""
        
        classification = self.intent_classifier.classify_intent(last_message)
        
        state.user_intent = classification["intent"]
        state.context.update({
            "classification": classification,
            "confidence": classification["confidence"]
        })
        
        return state
    
    def _route_by_intent(self, state) -> str:
        """Route to appropriate agent based on classified intent"""
        # Convert dict to ConversationState if needed  
        if isinstance(state, dict):
            state = ConversationState(**state)
        
        intent = state.user_intent or "GENERAL_CHAT"
        # Ensure consistent mapping
        intent_mapping = {
            "VIDEO_CRAWLING": "video_crawling",
            "KNOWLEDGE_QA": "knowledge_qa",
            "GENERAL_CHAT": "general_chat"
        }
        
        return intent_mapping.get(intent.upper(), "general_chat")
    
    def _video_crawling_node(self, state):
        """Node for video crawling agent"""
        # Convert dict to ConversationState if needed
        if isinstance(state, dict):
            state = ConversationState(**state)
        
        last_message = state.messages[-1]["content"] if state.messages else ""
        extracted_info = state.context.get("classification", {}).get("extracted_info", {})
        
        response = self.video_agent.process_crawling_request(last_message, extracted_info, state.user_id)
        
        state.messages.append({
            "role": "assistant",
            "content": response.message,
            "data": response.data,
            "timestamp": datetime.now().isoformat()
        })
        
        state.current_task = "video_crawling"
        return state
    
    def _knowledge_qa_node(self, state):
        """Node for knowledge Q&A agent"""
        # Convert dict to ConversationState if needed
        if isinstance(state, dict):
            state = ConversationState(**state)
        
        last_message = state.messages[-1]["content"] if state.messages else ""
        extracted_info = state.context.get("classification", {}).get("extracted_info", {})
        
        response = self.qa_agent.process_qa_request(last_message, extracted_info, state.user_id)
        
        state.messages.append({
            "role": "assistant", 
            "content": response.message,
            "data": response.data,
            "timestamp": datetime.now().isoformat()
        })
        
        state.current_task = "knowledge_qa"
        return state
    
    def _general_chat_node(self, state):
        """Node for general chat agent"""
        # Convert dict to ConversationState if needed
        if isinstance(state, dict):
            state = ConversationState(**state)
        
        last_message = state.messages[-1]["content"] if state.messages else ""
        
        response = self.chat_agent.process_general_chat(last_message, state.context)
        
        state.messages.append({
            "role": "assistant",
            "content": response.message, 
            "data": response.data,
            "timestamp": datetime.now().isoformat()
        })
        
        state.current_task = "general_chat"
        return state
    
    def process_user_message(self, user_message: str, user_id: str, session_id: str = None) -> Dict[str, Any]:
        """
        Process a user message through the orchestrated workflow
        
        Args:
            user_message: The user's input message
            user_id: User identifier
            session_id: Session identifier for conversation continuity
            
        Returns:
            Response containing assistant message and metadata
        """
        try:
            # Validate input
            is_valid, error_message = MessageValidator.validate_user_message(user_message)
            if not is_valid:
                return {
                    "success": False,
                    "message": f"Invalid input: {error_message}",
                    "error": error_message,
                    "task": TaskTypes.ERROR,
                    "timestamp": datetime.now().isoformat()
                }
            
            is_valid, error_message = MessageValidator.validate_session_data(user_id, session_id)
            if not is_valid:
                return {
                    "success": False,
                    "message": f"Invalid session data: {error_message}",
                    "error": error_message,
                    "task": TaskTypes.ERROR,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Create or update conversation state
            session_id = session_id or SessionManager.create_session_id(user_id)
            
            # Initialize state
            initial_state = SessionManager.create_initial_state(user_message, user_id, session_id)
            
            # Process through workflow
            config = {"configurable": {"thread_id": session_id}}
            # Convert to dict for workflow input, then convert result back
            workflow_input = initial_state.model_dump() if hasattr(initial_state, 'model_dump') else initial_state.__dict__
            result = self.workflow.invoke(workflow_input, config=config)
            # Convert result back to ConversationState if needed
            if isinstance(result, dict):
                result = ConversationState(**result)
            
            # Extract the assistant's response
            assistant_message = result.messages[-1]
            
            response = {
                "success": True,
                "message": assistant_message["content"],
                "data": assistant_message.get("data", {}),
                "session_id": session_id,
                "task": result.current_task,
                "user_intent": result.user_intent,
                "confidence": result.context.get("confidence", 0.0),
                "timestamp": assistant_message["timestamp"]
            }
            
            logger.info(f"Processed message for user {user_id}: intent={result.user_intent}, task={result.current_task}")
            return response
            
        except Exception as e:
            logger.error(f"Orchestrator failed: {e}")
            return {
                "success": False,
                "message": "I'm sorry, I encountered an error. Please try again.",
                "error": str(e),
                "session_id": session_id or SessionManager.create_session_id(user_id),
                "task": TaskTypes.ERROR,
                "timestamp": datetime.now().isoformat()
            }


# Convenience functions for easy integration

def create_chat_orchestrator(neo4j_client=None, user=None) -> ChatOrchestrator:
    """
    Create a new ChatOrchestrator instance
    
    Args:
        neo4j_client: Optional Neo4j client for knowledge graph access
        user: Optional Django User instance for database operations
        
    Returns:
        Configured ChatOrchestrator
    """
    return ChatOrchestrator(neo4j_client=neo4j_client, user=user)


def process_chat_message(user_message: str, user_id: str, session_id: str = None, 
                        orchestrator: ChatOrchestrator = None) -> Dict[str, Any]:
    """
    Process a single chat message through the orchestrator
    
    Args:
        user_message: User's message
        user_id: User identifier
        session_id: Optional session ID
        orchestrator: Optional pre-configured orchestrator
        
    Returns:
        Processing result
    """
    if orchestrator is None:
        orchestrator = create_chat_orchestrator()
    
    return orchestrator.process_user_message(user_message, user_id, session_id)


# Example usage for testing
if __name__ == "__main__":
    # Example conversation flow
    orchestrator = create_chat_orchestrator()
    
    test_messages = [
        "Hello! What can you do?",
        "Find videos about #machinelearning #AI",
        "What do my saved videos say about neural networks?",
        "Tìm video về #học_máy"
    ]
    
    user_id = "test_user_123"
    session_id = None
    
    for message in test_messages:
        print(f"\n🧑 User: {message}")
        
        response = orchestrator.process_user_message(message, user_id, session_id)
        session_id = response["session_id"]  # Continue conversation
        
        print(f"🤖 Assistant ({response['task']}, {response['user_intent']}):")
        print(response["message"])
        print(f"Confidence: {response['confidence']:.2f}")