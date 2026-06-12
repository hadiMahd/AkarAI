"""Unit tests for media validation helpers."""

import pytest

from app.common.media import (
    MediaValidationError,
    validate_file_type,
    validate_file_size,
    validate_image_dimensions,
    calculate_blur_score,
    validate_media_upload,
)


# Minimal valid image bytes for testing
JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00" * 16  # Minimal JPEG
PNG_HEADER = (
    b"\x89PNG\r\n\x1a\n"
    + b"\x00" * 8  # IHDR length/type placeholder
    + b"\x00" * 25  # More padding
)
WEBP_HEADER = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 20


class TestValidateFileType:
    def test_jpeg_detected(self):
        assert validate_file_type(JPEG_HEADER) == "image/jpeg"

    def test_png_detected(self):
        assert validate_file_type(PNG_HEADER) == "image/png"

    def test_webp_detected(self):
        assert validate_file_type(WEBP_HEADER) == "image/webp"

    def test_unsupported_type_raises(self):
        with pytest.raises(MediaValidationError, match="Unsupported file type"):
            validate_file_type(b"\x00\x00\x00\x00" * 10)

    def test_file_too_small_raises(self):
        with pytest.raises(MediaValidationError, match="too small"):
            validate_file_type(b"\xff\xd8\xff")

    def test_content_type_mismatch_raises(self):
        with pytest.raises(MediaValidationError, match="does not match"):
            validate_file_type(JPEG_HEADER, content_type="image/png")

    def test_content_type_match_succeeds(self):
        assert validate_file_type(JPEG_HEADER, content_type="image/jpeg") == "image/jpeg"


class TestValidateFileSize:
    def test_empty_file_raises(self):
        with pytest.raises(MediaValidationError, match="empty"):
            validate_file_size(b"")

    def test_valid_size_succeeds(self):
        validate_file_size(b"\x00" * 1024)  # Should not raise

    def test_oversized_file_raises(self):
        # Create a large file (simulate 11MB)
        large_data = b"\x00" * (11 * 1024 * 1024)
        with pytest.raises(MediaValidationError, match="exceeds maximum"):
            validate_file_size(large_data)


class TestValidateImageDimensions:
    def test_unsupported_format_raises(self):
        with pytest.raises(MediaValidationError, match="Unable to read"):
            validate_image_dimensions(b"\x00" * 100)


class TestCalculateBlurScore:
    def test_returns_float(self):
        # Will fallback to neutral score since PIL not available
        score = calculate_blur_score(JPEG_HEADER)
        assert isinstance(score, float)

    def test_returns_neutral_when_opencv_unavailable(self):
        # When OpenCV is not available, should return neutral score
        score = calculate_blur_score(JPEG_HEADER)
        assert score == 1000.0


class TestValidateMediaUpload:
    def test_valid_upload_returns_metadata(self):
        # PNG_HEADER should work since PNG parsing doesn't require Pillow
        result = validate_media_upload(PNG_HEADER, content_type="image/png")
        assert result["content_type"] == "image/png"
        assert result["file_size_bytes"] == len(PNG_HEADER)

    def test_empty_file_raises(self):
        with pytest.raises(MediaValidationError, match="empty"):
            validate_media_upload(b"")

    def test_unsupported_type_raises(self):
        with pytest.raises(MediaValidationError, match="Unsupported"):
            validate_media_upload(b"\x00" * 100)