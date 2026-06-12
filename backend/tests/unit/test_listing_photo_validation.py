"""Unit tests for listing photo validation and rejection behavior."""

import pytest

from app.common.media import (
    MediaValidationError,
    validate_file_type,
    validate_file_size,
    validate_media_upload,
)


class TestFileValidation:
    def test_valid_jpeg_accepted(self):
        jpeg_header = b"\xff\xd8\xff\xe0" + b"\x00" * 16
        result = validate_file_type(jpeg_header)
        assert result == "image/jpeg"

    def test_valid_png_accepted(self):
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 30
        result = validate_file_type(png_header)
        assert result == "image/png"

    def test_valid_webp_accepted(self):
        webp_header = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 20
        result = validate_file_type(webp_header)
        assert result == "image/webp"

    def test_gif_rejected(self):
        gif_header = b"GIF89a" + b"\x00" * 20
        with pytest.raises(MediaValidationError, match="Unsupported"):
            validate_file_type(gif_header)

    def test_bmp_rejected(self):
        bmp_header = b"BM" + b"\x00" * 30
        with pytest.raises(MediaValidationError, match="Unsupported"):
            validate_file_type(bmp_header)

    def test_empty_file_rejected(self):
        with pytest.raises(MediaValidationError, match="empty"):
            validate_file_size(b"")

    def test_oversized_file_rejected(self):
        large_data = b"\x00" * (11 * 1024 * 1024)  # 11MB
        with pytest.raises(MediaValidationError, match="exceeds maximum"):
            validate_file_size(large_data)

    def test_file_within_limit_accepted(self):
        valid_data = b"\x00" * (5 * 1024 * 1024)  # 5MB
        validate_file_size(valid_data)  # Should not raise


class TestUploadValidation:
    def test_valid_upload_returns_metadata(self):
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 30
        result = validate_media_upload(png_header, content_type="image/png")
        assert result["content_type"] == "image/png"
        assert result["file_size_bytes"] == len(png_header)

    def test_upload_with_content_type_mismatch_rejected(self):
        jpeg_header = b"\xff\xd8\xff\xe0" + b"\x00" * 16
        with pytest.raises(MediaValidationError, match="does not match"):
            validate_media_upload(jpeg_header, content_type="image/png")

    def test_upload_with_no_content_type_accepted(self):
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 30
        result = validate_media_upload(png_header)
        assert result["content_type"] == "image/png"