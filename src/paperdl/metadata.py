# ABOUTME: PDF metadata extraction and filename generation logic
# ABOUTME: Extracts titles/authors from PDFs and creates filesystem-safe names

def extract_metadata(pdf_path):
    """Extract title and author from PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        dict: Metadata containing title, authors, year
    """
    # TODO: Implement PDF text extraction with PyPDF2
    # TODO: Parse title and authors from first page
    # TODO: Extract year from text or filename
    raise NotImplementedError("Metadata extraction not yet implemented")


def generate_filename(metadata, original_filename):
    """Generate descriptive filename from metadata.
    
    Args:
        metadata: Dict with title, authors, year
        original_filename: Fallback filename
        
    Returns:
        str: Sanitized filename for filesystem
    """
    # TODO: Implement filename template: {year}-{author}-{title}.pdf
    # TODO: Sanitize special characters
    # TODO: Truncate long titles
    raise NotImplementedError("Filename generation not yet implemented")