from datetime import datetime, timedelta
from logging import getLogger
from typing import Optional

logger = getLogger(__name__)

class MessageValidator:
    """Utility class for validating messages and inputs"""
    
    @staticmethod
    def validate_user_message(message: str) -> tuple[bool, str]:
        """
        Validate user input message
        
        Returns:
            (is_valid, error_message)
        """
        if not message:
            return False, "Message cannot be empty"
        
        if not isinstance(message, str):
            return False, "Message must be a string"
        
        if len(message.strip()) == 0:
            return False, "Message cannot be only whitespace"
        
        if len(message) > 5000:  # Reasonable limit
            return False, "Message is too long (max 5000 characters)"
        
        return True, ""
    
    @staticmethod
    def validate_session_data(user_id: str, session_id: str = None) -> tuple[bool, str]:
        """
        Validate session data
        
        Returns:
            (is_valid, error_message)
        """
        if not user_id:
            return False, "User ID is required"
        
        if not isinstance(user_id, str):
            return False, "User ID must be a string"
        
        if session_id and not isinstance(session_id, str):
            return False, "Session ID must be a string"
        
        return True, ""


# Message type constants
class MessageTypes:
    """Constants for different message types"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Keywords:
    """Common keywords for parsing user queries"""

    # Platform keywords
    platform = {
        # "facebook": ["facebook", "fb", "meta"],
        # "instagram": ["instagram", "insta"],
        "tiktok": ["tiktok", "tt", "tik tok"],
        "bluesky": ["bluesky", "bs"],
        # "youtube": ["youtube", "yt"],
        # "twitter": ["twitter", "tweet", "x"],
    }

    # Time filter keywords for both English and Vietnamese
    time_filters = {
        "recent": { 
            "keywords":["recent", "latest", "new", "today", "yesterday", "gần đây", "mới nhất", "hôm nay", "hôm qua"],
            "days": 30 
            },
        "this_week": { 
            "keywords":["this week", "last week", "tuần này", "tuần trước"],
            "days": 7 
            },
    }

    # Keywords for increasing search scope
    broad_search = ["all", "everything", "summary", "overview", "tất cả", "toàn bộ", "tóm tắt", "khái quát"]

    @staticmethod
    def filter_keywords():
        """Flattened list of all filter keywords"""
        keywords = []
        for kw_list in Keywords.platform.values():
            keywords.extend(kw_list)
        for kw_list in Keywords.time_filters.values():
            keywords.extend(kw_list)
        return keywords
    
    @staticmethod
    def platform_keywords():
        """Flattened list of platform keywords"""
        keywords = []
        for kw_list in Keywords.platform.values():
            keywords.extend(kw_list)
        return keywords
    
    @staticmethod
    def time_filter_keywords():
        """Flattened list of time filter keywords"""
        keywords = []
        for kw_list in Keywords.time_filters.values():
            keywords.extend(kw_list)
        return keywords
    
    @staticmethod
    def filter_platform(query: str) -> Optional[list[str]]:
        """List of platforms mentioned in the query"""
        platforms = []
        query_lower = query.lower()
        for platform, kw_list in Keywords.platform.items():
            if any(kw in query_lower for kw in kw_list):
                platforms.append(platform)

        if not platforms:
            return None
        
        return platforms
    
    @staticmethod
    def filter_time(query: str) -> int:
        """Get timestamp filter based on time keywords in query. Returns Unix timestamp or None."""

        # Filter out times
        times = []
        query_lower = query.lower()
        for time_filter, data in Keywords.time_filters.items():
            if any(kw in query_lower for kw in data["keywords"]):
                times.append(time_filter)

        # Return timestamp if time filter found, otherwise None
        if not times:
            return int((datetime.now() - timedelta(days=30)).timestamp())
        
        days = 30
            
        if len(times) > 1:
            logger.info(f"Multiple time filters found in query: {times}. Using 'recent' (30 days).")
            days = Keywords.time_filters['recent']["days"]
        else:
            days = Keywords.time_filters[times[0]]["days"]
        
        return int((datetime.now() - timedelta(days=days)).timestamp())
    
    @staticmethod
    def is_broad_search(query: str) -> bool:
        """Check if the query indicates a broad search"""
        query_lower = query.lower()
        return any(word in query_lower for word in Keywords.broad_search)