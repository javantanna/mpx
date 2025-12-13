from typing import Optional, Dict

# EXCEPTION HIERARCHY
class MPXError(Exception):
    """Base exception for MPX operations"""

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
    

"""these classes will call __init__ of MPXError class"""
class ValidationError(MPXError):
    """Input validation failed"""
    pass


class EncodingError(MPXError):
    """Encoding operation failed"""
    pass


class DecodingError(MPXError):
    """Decoding operation failed"""
    pass


class IntegrityError(MPXError):
    """Integrity verification failed"""
    pass
