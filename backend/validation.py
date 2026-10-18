"""Input limits and checks for user-supplied chat text and images.

Side-effect free so it can be unit-tested without cloud credentials.
"""

ALLOWED_IMAGE_TYPES: frozenset[str] = frozenset({"image/jpeg", "image/png", "image/webp"})
MAX_IMAGE_BYTES: int = 10 * 1024 * 1024
MAX_MESSAGE_CHARS: int = 2000


def detect_image_type(data: bytes) -> str | None:
    """Returns the MIME type based on the file's magic bytes, or None if not allowed.

    The client-provided Content-Type is never trusted.
    """
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


async def read_capped(upload, limit: int) -> bytes:
    """Reads at most ``limit`` bytes from an UploadFile-like object.

    Raises ValueError if the content is longer than ``limit``, without
    reading more than ``limit + 1`` bytes into memory.
    """
    data = await upload.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"upload exceeds {limit} bytes")
    return data
