from langchain_core.tools import tool
import logging
from datetime import datetime, timedelta
from apps.agents.rag.utils import query_items
from .system_prompts import RAG_PROMPT
from .messages import Keywords
from ..kg_constructor.config import get_openai_llm

logger = logging.getLogger(__name__)

tools_llm = get_openai_llm(model="gpt-4o-mini")

@tool
def retrieve_and_answer(query: str, user_id: str, k: int = 5) -> str:
    """
    Retrieve relevant content from database, then generate an answer.
    
    Use this tool when users ask about their social content, saved content, or need 
    information from their personal content library. Works with TikTok and Facebook content.
    
    Args:
        query: User's question or query about their social content
        user_id: User identifier for personalized content access
        k: Number of top relevant items to retrieve (default: 5)
        
    Returns:
        Comprehensive answer based on retrieved content from social content library
    """
    try:        
        logger.info(f"RAG tool called with query: '{query}' for user: {user_id}")
        
        # Determine search parameters based on query content
        top_k = k
        platform_filter = None
        time_filter = None
        
        # Simple heuristics to improve search
        query_lower = query.lower()
        
        # Platform filtering
        platform_filters = Keywords.filter_platform(query)
        logger.info(f"Filtering for platforms: {platform_filters}")
        # Use first platform if multiple found
        if platform_filters:
            platform_filter = platform_filters[0]
        
        # Time filtering for recent content (returns timestamp)
        time_filter = Keywords.filter_time(query)
        logger.info(f"Filtering for content from timestamp: {time_filter}")
        
        # Increase search results for broad queries
        if Keywords.is_broad_search(query):
            top_k = 10

        # Query Milvus for relevant content
        search_results = query_items(
            user_id=user_id,
            query=query,
            top_k=top_k,
            from_timestamp=time_filter,
            platform=platform_filter
        )
        
        results = search_results.get("results", [])
        filter_info = search_results.get("filter", "")
        
        if not results:
            filter_msg = ""
            if platform_filter:
                filter_msg += f" on {platform_filter.title()}"
            if time_filter:
                filter_msg += f" from recent content"
                
            return (
                f"I couldn't find any relevant content{filter_msg} in your social media library for: '{query}'. "
                f"This might be because:\n"
                f"• No content has been saved yet{filter_msg}\n"
                f"• The query doesn't match any of your saved content\n"
                f"• Try rephrasing your question or asking about different topics\n"
                f"• If you used filters (recent, TikTok, Facebook), try broadening your search"
            )
        
        # Prepare context from retrieved content with enhanced formatting
        context_pieces = []
        platforms_found = set()
        
        for i, result in enumerate(results, 1):
            content_url = result.get('content_url', 'N/A')
            platform = result.get('platform', 'Unknown').title()
            summary = result.get('summary', 'No summary available')
            score = result.get('score', 0.0)
            timestamp = result.get('timestamp', 0)
            
            platforms_found.add(platform)
            
            # Format timestamp if available
            date_str = ""
            if timestamp:
                try:
                    date_obj = datetime.fromtimestamp(timestamp)
                    date_str = f" from {date_obj.strftime('%Y-%m-%d')}"
                except:
                    date_str = ""
            
            context_pieces.append(
                f"Content {i} ({platform}{date_str} from URL: {content_url}, relevance: {score:.3f}):\n{summary}"
            )
        
        context = "\n\n".join(context_pieces)
        
        # Enhanced metadata for the answer
        search_meta = f"Found {len(results)} relevant items"
        if platforms_found:
            search_meta += f" across {', '.join(sorted(platforms_found))}"
        if time_filter:
            search_meta += " from recent content"
        
        # Use LLM to generate answer based on retrieved content
        llm = tools_llm
        
        response = llm.invoke([{"role": "user", "content": RAG_PROMPT.format(
            query=query, 
            search_meta=search_meta, 
            context=context)
            }])
        answer = response.content if hasattr(response, 'content') else str(response)
        
        logger.info(f"RAG tool successfully generated answer for user {user_id} with {len(results)} results")
        return answer
        
    except ImportError as e:
        logger.error(f"RAG dependencies not available: {e}")
        return (
            f"The content search feature is not available right now due to missing dependencies. "
            f"Please check that the RAG system is properly configured."
        )
    except Exception as e:
        logger.error(f"RAG tool failed for user {user_id} with query '{query}': {e}")
        return (
            f"I encountered an error while searching your content library: {str(e)}. "
            f"Please try again or rephrase your question. If the problem persists, "
            f"the search system may need to be configured or your content library may be empty."
        )