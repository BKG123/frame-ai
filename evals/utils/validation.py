"""
Utility functions for evaluations
"""

import json
from typing import Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path


def validate_json_structure(
    response_text: str, expected_schema: Dict
) -> Tuple[bool, str]:
    """
    Validate that the response is valid JSON and matches expected schema.

    Args:
        response_text: The raw response text to validate
        expected_schema: Dictionary defining expected structure

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"

    # Check top-level fields
    for key, value_type in expected_schema.items():
        if key not in data:
            return False, f"Missing required field: {key}"

        if isinstance(value_type, dict):
            # Nested structure validation
            if not isinstance(data[key], dict):
                return False, f"Field '{key}' should be a dictionary"

            for nested_key, nested_type in value_type.items():
                if nested_key not in data[key]:
                    return False, f"Missing nested field: {key}.{nested_key}"

                if not isinstance(data[key][nested_key], nested_type):
                    return (
                        False,
                        f"Field '{key}.{nested_key}' should be type {nested_type.__name__}",
                    )
        else:
            # Simple type validation
            if not isinstance(data[key], value_type):
                return False, f"Field '{key}' should be type {value_type.__name__}"

    return True, ""


def check_content_quality(
    data: Dict[str, Any], min_length: int, max_length: int
) -> List[str]:
    """
    Check basic content quality metrics.

    Args:
        data: Parsed JSON response
        min_length: Minimum acceptable length for text fields
        max_length: Maximum acceptable length for overall impression

    Returns:
        List of error messages (empty if all checks pass)
    """
    errors = []

    # Check overall impression length
    impression = data.get("overall_impression", "")
    if len(impression) < min_length:
        errors.append(f"Overall impression too short ({len(impression)} chars)")
    elif len(impression) > max_length:
        errors.append(f"Overall impression too long ({len(impression)} chars)")

    # Check bullet points are non-empty
    bullet_points = data.get("concise_bullet_points", {})
    for field in ["technical", "artistic", "best_practice", "next_step"]:
        content = bullet_points.get(field, "")
        if len(content) < min_length:
            errors.append(
                f"Bullet point '{field}' too short or empty ({len(content)} chars)"
            )

    return errors


def check_exif_awareness(
    response_text: str, has_exif: bool, exif_keywords: List[str]
) -> bool:
    """
    Check if response appropriately handles EXIF data.

    Args:
        response_text: The full response text
        has_exif: Whether the input image had EXIF data
        exif_keywords: List of keywords that should appear when EXIF is present

    Returns:
        True if EXIF handling is appropriate
    """
    response_lower = response_text.lower()

    if has_exif:
        # If EXIF data was provided, response should mention camera settings
        return any(keyword in response_lower for keyword in exif_keywords)
    else:
        # If no EXIF data, it's okay either way (not required to mention it)
        return True


def save_eval_result(
    test_name: str, passed: bool, details: Dict[str, Any], results_dir: Path
):
    """
    Save evaluation result to a JSON file with timestamp.

    Args:
        test_name: Name of the test
        passed: Whether the test passed
        details: Additional details about the test
        results_dir: Directory to save results
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {
        "test_name": test_name,
        "timestamp": timestamp,
        "passed": passed,
        "details": details,
    }

    result_file = results_dir / f"{test_name}_{timestamp}.json"
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)

    return result_file


def calculate_pass_rate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate aggregate pass rate from list of results.

    Args:
        results: List of test result dictionaries

    Returns:
        Dictionary with pass rate statistics
    """
    total = len(results)
    passed = sum(1 for r in results if r.get("passed", False))

    return {
        "total_tests": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": (passed / total * 100) if total > 0 else 0,
    }
