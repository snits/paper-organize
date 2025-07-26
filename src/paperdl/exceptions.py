# ABOUTME: Custom exception classes for paper-dl error handling
# ABOUTME: Defines specific error types for different failure modes


class PaperDLError(Exception):
    """Base exception for paper-dl errors."""


class DownloadError(PaperDLError):
    """Error during file download."""


class MetadataError(PaperDLError):
    """Error during PDF metadata extraction."""


class StorageError(PaperDLError):
    """Error during file storage operations."""
