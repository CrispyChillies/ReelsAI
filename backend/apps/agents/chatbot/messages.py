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