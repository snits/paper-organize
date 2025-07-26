# ABOUTME: Custom exception classes for paper-dl error handling
# ABOUTME: Defines specific error types with user-friendly messages and debugging details

from typing import Dict, Any, Optional


class PaperDLError(Exception):
    """Base exception for paper-dl errors.
    
    Provides structured error handling with user-friendly messages
    and debugging details.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def user_message(self) -> str:
        """Return a user-friendly error message."""
        return self.message


class NetworkError(PaperDLError):
    """Network-related errors during download operations."""
    
    def user_message(self) -> str:
        """Return a user-friendly network error message."""
        return f"Network error: {self.message}"


class HTTPError(NetworkError):
    """HTTP-specific errors with status code information."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 url: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if status_code is not None:
            details['status_code'] = status_code
        if url is not None:
            details['url'] = url
        super().__init__(message, details)
        self.status_code = status_code
        self.url = url
    
    def user_message(self) -> str:
        """Return a user-friendly HTTP error message."""
        if self.status_code:
            return f"HTTP {self.status_code}: {self.message}"
        return f"HTTP error: {self.message}"


class FileSystemError(PaperDLError):
    """File system operation errors."""
    
    def __init__(self, message: str, path: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if path is not None:
            details['path'] = path
        super().__init__(message, details)
        self.path = path
    
    def user_message(self) -> str:
        """Return a user-friendly file system error message."""
        if self.path:
            return f"File system error with '{self.path}': {self.message}"
        return f"File system error: {self.message}"


class ValidationError(PaperDLError):
    """Input validation and data format errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 value: Optional[Any] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if field is not None:
            details['field'] = field
        if value is not None:
            details['value'] = value
        super().__init__(message, details)
        self.field = field
        self.value = value
    
    def user_message(self) -> str:
        """Return a user-friendly validation error message."""
        if self.field:
            return f"Invalid {self.field}: {self.message}"
        return f"Validation error: {self.message}"


# Legacy aliases for backward compatibility
DownloadError = NetworkError
MetadataError = ValidationError
StorageError = FileSystemError
