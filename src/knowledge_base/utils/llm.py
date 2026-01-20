"""
LLM response parsing utilities.
Provides robust parsing for LLM responses with JSON extraction.
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def extract_json_from_llm_response(content: str) -> dict[str, Any] | None:
    """
    Extract JSON from LLM response content.

    This function handles various JSON formats that LLMs might return:
    - Plain JSON
    - JSON wrapped in markdown code blocks
    - JSON with leading/trailing text
    - JSON with comments

    Args:
        content: The LLM response content

    Returns:
        Parsed JSON dictionary or None if parsing fails
    """
    if not content:
        logger.warning("Empty content provided to extract_json_from_llm_response")
        return None

    content = content.strip()

    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from code block: {e}")
            # Continue to try other methods

    # Try to extract JSON using regex for outermost braces
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from regex match: {e}")

    # Try to parse the entire content as JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse content as JSON: {e}")
        return None


def clean_llm_response(content: str) -> str:
    """
    Clean LLM response by removing common artifacts.

    Removes:
    - Markdown code blocks
    - Leading/trailing whitespace
    - Common LLM artifacts

    Args:
        content: The LLM response content

    Returns:
        Cleaned content string
    """
    if not content:
        return ""

    # Remove markdown code blocks
    content = re.sub(r"```(?:json)?\s*", "", content)
    content = re.sub(r"```", "", content)

    # Remove common artifacts
    content = re.sub(r"Here's the JSON:", "", content, flags=re.IGNORECASE)
    content = re.sub(r"JSON response:", "", content, flags=re.IGNORECASE)
    content = re.sub(r"Result:", "", content, flags=re.IGNORECASE)

    return content.strip()


def validate_json_structure(data: dict[str, Any], required_keys: list[str]) -> bool:
    """
    Validate that JSON contains required keys.

    Args:
        data: Parsed JSON dictionary
        required_keys: List of required keys

    Returns:
        True if all required keys are present, False otherwise
    """
    if not isinstance(data, dict):
        return False

    return all(key in data for key in required_keys)


def safe_json_loads(content: str, default: Any = None) -> Any:
    """
    Safely load JSON with fallback to default value.

    Args:
        content: JSON string to parse
        default: Default value if parsing fails

    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON: {e}, returning default")
        return default
