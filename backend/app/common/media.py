"""Media validation helpers for listing photo upload and processing."""

import io
import struct
from pathlib import Path

from app.common.config import settings


# Allowed MIME types and their magic bytes signatures
ALLOWED_SIGNATURES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp",
}

MAX_FILE_SIZE_BYTES = settings.media_max_file_size_mb * 1024 * 1024


class MediaValidationError(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


def validate_file_type(file_bytes: bytes, content_type: str | None = None) -> str:
    """Validate file type by magic bytes. Returns confirmed MIME type."""
    if len(file_bytes) < 12:
        raise MediaValidationError("File is too small to be a valid image")

    mime = None

    # Check JPEG signature (3 bytes)
    if file_bytes[:3] == b"\xff\xd8\xff":
        mime = "image/jpeg"
    # Check PNG signature (8 bytes)
    elif file_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        mime = "image/png"
    # Check WebP (RIFF + 4 bytes + WEBP)
    elif file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP":
        mime = "image/webp"

    if mime is None:
        raise MediaValidationError(
            f"Unsupported file type. Allowed: {', '.join(ALLOWED_SIGNATURES.values())}"
        )

    # If content_type was provided, verify it matches
    if content_type and content_type.lower() != mime:
        raise MediaValidationError(
            f"Content-Type header '{content_type}' does not match file content"
        )

    return mime


def validate_file_size(file_bytes: bytes) -> None:
    """Validate file size is within limits."""
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        max_mb = settings.media_max_file_size_mb
        raise MediaValidationError(
            f"File size exceeds maximum allowed size of {max_mb}MB"
        )
    if len(file_bytes) == 0:
        raise MediaValidationError("Uploaded file is empty")


def validate_image_dimensions(file_bytes: bytes) -> tuple[int, int]:
    """Extract image dimensions. Returns (width, height)."""
    try:
        # Try PIL first
        from PIL import Image
        img = Image.open(io.BytesIO(file_bytes))
        return img.size
    except ImportError:
        pass
    except Exception:
        raise MediaValidationError("Unable to read image dimensions")

    try:
        # Try struct-based parsing for PNG
        if file_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            ihdr = file_bytes[16:24]
            w, h = struct.unpack(">II", ihdr)
            return w, h
        # JPEG dimensions require parsing SOF marker (simplified)
        if file_bytes[:3] == b"\xff\xd8\xff":
            raise MediaValidationError("JPEG dimension extraction requires Pillow")
    except MediaValidationError:
        raise
    except Exception:
        pass

    raise MediaValidationError("Unable to read image dimensions")


def calculate_blur_score(file_bytes: bytes) -> float:
    """Calculate blur score using Laplacian variance.

    Higher values = sharper. Lower values = blurrier.
    Returns the Laplacian variance as a float.
    """
    try:
        import cv2
        import numpy as np
        from PIL import Image

        img = Image.open(io.BytesIO(file_bytes)).convert("L")
        img_array = np.array(img)

        # Apply Laplacian filter
        laplacian = cv2.Laplacian(img_array, cv2.CV_64F)
        variance = laplacian.var()

        return float(variance)
    except ImportError:
        # Fallback: return a neutral score if OpenCV is not available
        return 1000.0
    except Exception:
        # On error, return neutral score
        return 1000.0


def is_blurry(file_bytes: bytes) -> bool:
    """Check if image is blurry based on threshold."""
    score = calculate_blur_score(file_bytes)
    return score < settings.media_blur_threshold


def validate_media_upload(file_bytes: bytes, content_type: str | None = None) -> dict:
    """Run full upload validation. Returns metadata dict or raises."""
    validate_file_size(file_bytes)
    mime = validate_file_type(file_bytes, content_type)
    width, height = validate_image_dimensions(file_bytes)

    return {
        "content_type": mime,
        "file_size_bytes": len(file_bytes),
        "width": width,
        "height": height,
    }


def process_image_for_derivative(
    file_bytes: bytes,
    max_width: int | None = None,
    quality: int | None = None,
) -> tuple[bytes, int, int]:
    """Process image to create optimized WebP derivative.

    Returns (processed_bytes, width, height).
    """
    from PIL import Image

    max_width = max_width or settings.media_derivative_max_width
    quality = quality or settings.media_derivative_quality

    img = Image.open(io.BytesIO(file_bytes))

    # Convert RGBA to RGB if needed (WebP with transparency not needed for listing display)
    if img.mode in ("RGBA", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background

    # Resize if width exceeds max
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    # Save as WebP
    output = io.BytesIO()
    img.save(output, format="WEBP", quality=quality)
    output.seek(0)

    return output.getvalue(), img.width, img.height