"""Unit tests for listing photo processing (quality scoring and derivative generation)."""

import pytest
from unittest.mock import patch

from app.common.media import calculate_blur_score, is_blurry, process_image_for_derivative
from app.common.config import settings


class TestQualityScoring:
    def test_calculate_blur_score_returns_float(self):
        """Test that blur score returns a float value."""
        # Use a minimal PNG header
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 30
        score = calculate_blur_score(png_data)
        assert isinstance(score, float)

    def test_calculate_blur_score_returns_neutral_when_opencv_unavailable(self):
        """Test that neutral score is returned when OpenCV is not available."""
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 30
        score = calculate_blur_score(png_data)
        # When OpenCV is not available, should return neutral score
        assert score == 1000.0

    def test_is_blurry_returns_bool(self):
        """Test that is_blurry returns a boolean."""
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 30
        result = is_blurry(png_data)
        assert isinstance(result, bool)

    def test_blur_threshold_is_calibrated_value(self):
        """Test that the blur threshold is set to the calibrated value."""
        assert settings.media_blur_threshold == 208.12155306730278

    def test_is_blurry_below_threshold(self):
        """Test that scores below threshold are detected as blurry."""
        with patch("app.common.media.calculate_blur_score") as mock_score:
            mock_score.return_value = 100.0  # Below threshold
            assert is_blurry(b"dummy") is True

    def test_is_blurry_above_threshold(self):
        """Test that scores above threshold are not detected as blurry."""
        with patch("app.common.media.calculate_blur_score") as mock_score:
            mock_score.return_value = 500.0  # Above threshold
            assert is_blurry(b"dummy") is False

    def test_is_blurry_at_threshold_exact(self):
        """Test that score exactly at threshold is not blurry (>= threshold = sharp)."""
        with patch("app.common.media.calculate_blur_score") as mock_score:
            mock_score.return_value = settings.media_blur_threshold
            assert is_blurry(b"dummy") is False


class TestDerivativeGeneration:
    def test_process_image_for_derivative_returns_tuple(self):
        """Test that derivative generation returns (bytes, width, height)."""
        # This will fail without PIL, but we can test the function signature
        try:
            from PIL import Image
            import io

            # Create a minimal valid image
            img = Image.new("RGB", (100, 100), color="red")
            output = io.BytesIO()
            img.save(output, format="PNG")
            img_bytes = output.getvalue()

            result_bytes, width, height = process_image_for_derivative(img_bytes)
            assert isinstance(result_bytes, bytes)
            assert isinstance(width, int)
            assert isinstance(height, int)
            assert width <= 1920  # max_width default
        except ImportError:
            # PIL not available in test environment
            pass

    def test_process_image_for_derivative_max_width_respected(self):
        """Test that max_width parameter is respected."""
        try:
            from PIL import Image
            import io

            # Create a wide image
            img = Image.new("RGB", (3000, 500), color="blue")
            output = io.BytesIO()
            img.save(output, format="PNG")
            img_bytes = output.getvalue()

            result_bytes, width, height = process_image_for_derivative(img_bytes, max_width=1000)
            assert width <= 1000
        except ImportError:
            pass

    def test_process_image_for_derivative_quality_parameter(self):
        """Test that quality parameter affects output size."""
        try:
            from PIL import Image
            import io

            img = Image.new("RGB", (200, 200), color="green")
            output = io.BytesIO()
            img.save(output, format="PNG")
            img_bytes = output.getvalue()

            # High quality should produce larger file
            result_high, _, _ = process_image_for_derivative(img_bytes, quality=95)
            result_low, _, _ = process_image_for_derivative(img_bytes, quality=50)

            assert len(result_high) >= len(result_low)
        except ImportError:
            pass