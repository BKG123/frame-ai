"""
Comprehensive tests for Frame AI photo analysis.

This module tests the photo analysis system against real images,
validating JSON structure, content quality, and analysis depth.
"""

import json
import pytest
import pytest_asyncio

from evals.config import (
    EXPECTED_JSON_SCHEMA,
    MIN_OVERALL_IMPRESSION_LENGTH,
    MAX_OVERALL_IMPRESSION_LENGTH,
    MIN_BULLET_POINT_LENGTH,
)
from evals.utils import (
    validate_json_structure,
    check_content_quality,
)


@pytest.mark.asyncio
class TestPhotoAnalysis:
    """Comprehensive photo analysis validation tests."""

    # ===========================================
    # JSON Structure & Format Tests
    # ===========================================

    async def test_produces_valid_json(self, analysis_response: str):
        """Test that analysis produces valid JSON."""
        try:
            data = json.loads(analysis_response)
            assert data is not None, "Response should parse to valid JSON"
        except json.JSONDecodeError as e:
            pytest.fail(f"Analysis produced invalid JSON: {e}")

    async def test_has_required_structure(self, analysis_response: str):
        """Test that analysis has all required fields."""
        is_valid, error = validate_json_structure(
            analysis_response, EXPECTED_JSON_SCHEMA
        )
        assert is_valid, f"Schema validation failed: {error}"

    async def test_overall_impression_exists(self, analysis_data: dict):
        """Test that overall_impression field exists and is a string."""
        assert "overall_impression" in analysis_data
        assert isinstance(analysis_data["overall_impression"], str)

    async def test_bullet_points_structure(self, analysis_data: dict):
        """Test that concise_bullet_points has correct nested structure."""
        assert "concise_bullet_points" in analysis_data
        bullet_points = analysis_data["concise_bullet_points"]

        required_fields = ["technical", "artistic", "best_practice", "next_step"]
        for field in required_fields:
            assert field in bullet_points, f"Missing required field: {field}"
            assert isinstance(bullet_points[field], str), (
                f"Field {field} should be a string"
            )

    # ===========================================
    # Content Quality Tests
    # ===========================================

    async def test_content_quality_standards(self, analysis_data: dict):
        """Test that analysis meets content quality standards."""
        errors = check_content_quality(
            analysis_data,
            MIN_BULLET_POINT_LENGTH,
            MAX_OVERALL_IMPRESSION_LENGTH,
        )
        assert not errors, f"Content quality issues: {'; '.join(errors)}"

    async def test_overall_impression_length(self, analysis_data: dict):
        """Test that overall impression is within acceptable length range."""
        impression = analysis_data["overall_impression"]
        assert len(impression) >= MIN_OVERALL_IMPRESSION_LENGTH, (
            f"Overall impression too short: {len(impression)} chars"
        )
        assert len(impression) <= MAX_OVERALL_IMPRESSION_LENGTH, (
            f"Overall impression too long: {len(impression)} chars"
        )

    async def test_no_placeholder_text(self, analysis_response: str):
        """Test that response doesn't contain obvious placeholder text."""
        placeholders = [
            "TODO",
            "TBD",
            "PLACEHOLDER",
            "[insert",
            "lorem ipsum",
            "xxx",
        ]

        response_lower = analysis_response.lower()
        found_placeholders = [p for p in placeholders if p.lower() in response_lower]

        assert not found_placeholders, (
            f"Found placeholder text: {', '.join(found_placeholders)}"
        )

    async def test_all_sections_unique(self, analysis_data: dict):
        """Test that all sections have unique content."""
        bullet_points = analysis_data.get("concise_bullet_points", {})

        sections = [
            bullet_points.get("technical", "").strip().lower(),
            bullet_points.get("artistic", "").strip().lower(),
            bullet_points.get("best_practice", "").strip().lower(),
            bullet_points.get("next_step", "").strip().lower(),
        ]

        # Check no two sections are identical
        for i, section1 in enumerate(sections):
            for section2 in sections[i + 1 :]:
                assert section1 != section2, (
                    "Different sections should not have identical content"
                )

    # ===========================================
    # Content Depth & Quality Tests
    # ===========================================

    async def test_meaningful_impression(self, analysis_data: dict):
        """Test that overall impression is meaningful and specific."""
        impression = analysis_data.get("overall_impression", "")

        # Should be substantial
        assert len(impression) >= MIN_OVERALL_IMPRESSION_LENGTH, (
            f"Overall impression too short: {len(impression)} chars"
        )

        # Should not be overly generic
        generic_phrases = [
            "this is a photo",
            "this is an image",
            "this picture shows",
        ]
        impression_lower = impression.lower()
        generic_count = sum(
            1 for phrase in generic_phrases if phrase in impression_lower
        )

        # Allow some generic language, but not exclusively
        assert len(impression) > 50 or generic_count == 0, (
            "Overall impression seems too generic"
        )

    async def test_technical_feedback_depth(self, analysis_data: dict):
        """Test that technical feedback is substantial and specific."""
        technical = analysis_data.get("concise_bullet_points", {}).get("technical", "")

        assert len(technical) >= MIN_BULLET_POINT_LENGTH, "Technical feedback missing"

        # Should mention at least some technical aspect
        technical_terms = [
            "exposure",
            "focus",
            "aperture",
            "iso",
            "shutter",
            "noise",
            "sharpness",
            "depth of field",
            "bokeh",
            "lighting",
            "contrast",
            "white balance",
        ]

        technical_lower = technical.lower()
        has_technical_term = any(term in technical_lower for term in technical_terms)

        assert has_technical_term, (
            "Technical feedback should mention at least one technical aspect"
        )

    async def test_artistic_feedback_depth(self, analysis_data: dict):
        """Test that artistic feedback covers compositional elements."""
        artistic = analysis_data.get("concise_bullet_points", {}).get("artistic", "")

        assert len(artistic) >= MIN_BULLET_POINT_LENGTH, "Artistic feedback missing"

        # Should mention compositional elements
        compositional_terms = [
            "composition",
            "framing",
            "rule of thirds",
            "leading lines",
            "symmetry",
            "balance",
            "perspective",
            "subject",
            "background",
            "foreground",
            "color",
            "mood",
            "emotion",
        ]

        artistic_lower = artistic.lower()
        has_compositional_term = any(
            term in artistic_lower for term in compositional_terms
        )

        assert has_compositional_term, (
            "Artistic feedback should mention compositional elements"
        )

    async def test_actionable_next_step(self, analysis_data: dict):
        """Test that next_step provides actionable advice."""
        next_step = analysis_data.get("concise_bullet_points", {}).get("next_step", "")

        assert len(next_step) >= MIN_BULLET_POINT_LENGTH, "Next step missing"

        # Should have actionable language
        actionable_words = [
            "try",
            "consider",
            "use",
            "adjust",
            "experiment",
            "shoot",
            "focus",
            "look for",
            "avoid",
            "practice",
        ]

        next_step_lower = next_step.lower()
        has_actionable = any(word in next_step_lower for word in actionable_words)

        assert has_actionable, "Next step should provide actionable advice"


# ===========================================
# Fixtures
# ===========================================


@pytest_asyncio.fixture
async def analysis_response(fixtures_dir) -> str:
    """
    Run actual photo analysis on first available test image.

    This fixture performs real LLM analysis and is slower than mock data.
    """
    from services.analysis import PhotoAnalyzer

    # Find test images
    images_dir = fixtures_dir / "images"
    test_images = (
        list(images_dir.glob("*.jpg"))
        + list(images_dir.glob("*.jpeg"))
        + list(images_dir.glob("*.png"))
    )

    if not test_images:
        pytest.skip("No test images found in fixtures/images directory")

    # Use first test image
    test_image = str(test_images[0])
    print(f"\n🔍 Analyzing: {test_images[0].name}")

    # Run analysis
    analyzer = PhotoAnalyzer()
    stream_chunks = []

    async for chunk in analyzer.analyze_photo_from_file_stream(test_image):
        stream_chunks.append(chunk)

    full_output = "".join(stream_chunks)
    print(f"✅ Analysis complete ({len(full_output)} chars)")

    # Extract JSON portion
    json_marker = "*#123JSON PARSING START: "
    if json_marker in full_output:
        json_part = full_output.split(json_marker, 1)[1].strip()
    else:
        # Try to find JSON in output
        start_idx = full_output.find("{")
        end_idx = full_output.rfind("}") + 1
        if start_idx != -1 and end_idx > start_idx:
            json_part = full_output[start_idx:end_idx]
        else:
            pytest.fail("Could not extract JSON from analysis output")

    # Remove markdown code blocks if present
    if json_part.startswith("```json"):
        json_part = json_part.replace("```json", "", 1)
    if json_part.startswith("```"):
        json_part = json_part.replace("```", "", 1)
    if json_part.endswith("```"):
        json_part = json_part.rsplit("```", 1)[0]

    json_part = json_part.strip()

    return json_part


@pytest_asyncio.fixture
async def analysis_data(analysis_response: str) -> dict:
    """Parse analysis response to dictionary."""
    return json.loads(analysis_response)


@pytest.fixture
def fixtures_dir():
    """Fixture providing path to fixtures directory."""
    from evals.config import EVALS_DIR

    return EVALS_DIR / "fixtures"
