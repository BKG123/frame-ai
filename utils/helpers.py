"""Common helper functions used across the application."""

import hashlib
import mimetypes


def clean_json_response(json_str: str) -> str:
    """
    Remove markdown code blocks from JSON string responses.

    This function handles common formatting issues where LLMs return JSON
    wrapped in markdown code fences like ```json ... ```.

    Args:
        json_str: Raw JSON string potentially containing markdown formatting

    Returns:
        Cleaned JSON string ready for parsing

    Example:
        >>> clean_json_response('```json\\n{"key": "value"}\\n```')
        '{"key": "value"}'
    """
    json_str = json_str.strip()
    if json_str.startswith("```json"):
        json_str = json_str[7:]
    if json_str.startswith("```"):
        json_str = json_str[3:]
    if json_str.endswith("```"):
        json_str = json_str[:-3]
    return json_str.strip()


def get_file_mime_type(file_path: str) -> str:
    """
    Get MIME type of a file from its path or extension.

    Args:
        file_path: Path to the file

    Returns:
        MIME type string (e.g., 'image/jpeg') or 'application/octet-stream' if unknown

    Example:
        >>> get_file_mime_type('/path/to/image.jpg')
        'image/jpeg'
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def get_content_hash(file_content: bytes) -> str:
    """
    Generate SHA-256 hash from file content for cache key and deduplication.

    This ensures:
    - Same image content = same hash (deduplication)
    - Different images with same filename = different hashes (correctness)
    - No PII (IP addresses) in cache keys (privacy)

    Args:
        file_content: Raw bytes of the uploaded file

    Returns:
        Hex string of SHA-256 hash (64 characters)

    Example:
        >>> get_content_hash(b'test content')
        '6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72'
    """
    return hashlib.sha256(file_content).hexdigest()


def get_filename_hash(filename: str) -> str:
    """
    Generate MD5 hash from filename string.

    Note: This is legacy and should be replaced with content-based hashing
    for better deduplication. Kept for backward compatibility.

    Args:
        filename: Name of the file

    Returns:
        Hex string of MD5 hash (32 characters)

    Example:
        >>> get_filename_hash('example.jpg')
        '9bce13c8b4cdb8f0c7dfc8e0e69f9b02'
    """
    return hashlib.md5(filename.encode()).hexdigest()
