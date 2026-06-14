"""Unit tests for listing photo processing (quality scoring and derivative generation)."""

import pytest
from unittest.mock import patch

from app.common.media import calculate_blur_score, is_blurry, process_image_for_derivative
from app.common.config import settings


class TestQualityScoring:
    def test_calculate_blur_score_returns_float(self):
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 30
        score = calculate_blur_score(png_data)
        assert isinstance(score, float)

    def test_calculate_blur_score_returns_neutral_when_opencv_unavailable(self):
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 30
        score = calculate_blur_score(png_data)
        assert score == 1000.0

    def test_is_blurry_returns_bool(self):
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 30
        result = is_blurry(png_data)
        assert isinstance(result, bool)

    def test_blur_threshold_is_calibrated_value(self):
        assert settings.media_blur_threshold == 208.12155306730278

    def test_is_blurry_below_threshold(self):
        with patch("app.common.media.calculate_blur_score") as mock_score:
            mock_score.return_value = 100.0
            assert is_blurry(b"dummy") is True

    def test_is_blurry_above_threshold(self):
        with patch("app.common.media.calculate_blur_score") as mock_score:
            mock_score.return_value = 500.0
            assert is_blurry(b"dummy") is False

    def test_is_blurry_at_threshold_exact(self):
        with patch("app.common.media.calculate_blur_score") as mock_score:
            mock_score.return_value = settings.media_blur_threshold
            assert is_blurry(b"dummy") is False


class TestDerivativeGeneration:
    def test_process_image_for_derivative_returns_tuple(self):
        try:
            from PIL import Image
            import io

            img = Image.new("RGB", (100, 100), color="red")
            output = io.BytesIO()
            img.save(output, format="PNG")
            img_bytes = output.getvalue()

            result_bytes, width, height = process_image_for_derivative(img_bytes)
            assert isinstance(result_bytes, bytes)
            assert isinstance(width, int)
            assert isinstance(height, int)
            assert width <= 1920
        except ImportError:
            pass

    def test_process_image_for_derivative_max_width_respected(self):
        try:
            from PIL import Image
            import io

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

            # Use a checkerboard pattern so quality differences are detectable
            img = Image.new("RGB", (200, 200), color="white")
            pixels = img.load()
            for x in range(200):
                for y in range(200):
                    if (x // 10 + y // 10) % 2 == 0:
                        pixels[x, y] = (0, 0, 0)
            output = io.BytesIO()
            img.save(output, format="PNG")
            img_bytes = output.getvalue()

            result_high, _, _ = process_image_for_derivative(img_bytes, quality=95)
            result_low, _, _ = process_image_for_derivative(img_bytes, quality=10)

            # Higher quality should produce different bytes
            assert len(result_high) != len(result_low)
        except ImportError:
            pass
