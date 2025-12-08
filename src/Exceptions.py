from typing import Optional, Dict

# EXCEPTION HIERARCHY
class MP5Error(Exception):
    """Base exception for MP5 operations"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message=message
        self.details=details or {}
        super().__init__(self.message)


    def to_dict(self)-> Dict:
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }
    

"""these classes will call __init__ of MP5Error class"""
class ValidationError(MP5Error):
    """Input validation failed"""
    pass


class EncodingError(MP5Error):
    """Encoding operation failed"""
    pass


class DecodingError(MP5Error):
    """Decoding operation failed"""
    pass


class IntegrityError(MP5Error):
    """Integrity verification failed"""
    pass
