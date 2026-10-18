import unittest

from validation import detect_image_type, read_capped

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 10
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 10
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"0" * 10


class DetectImageTypeTest(unittest.TestCase):
    def test_known_types(self):
        self.assertEqual(detect_image_type(JPEG), "image/jpeg")
        self.assertEqual(detect_image_type(PNG), "image/png")
        self.assertEqual(detect_image_type(WEBP), "image/webp")

    def test_rejects_others(self):
        for data in (b"%PDF-1.7", b"GIF89a", b"", b"RIFF\x00\x00\x00\x00WAVE"):
            self.assertIsNone(detect_image_type(data))


class _Upload:
    """Minimal stand-in for fastapi.UploadFile.read()."""

    def __init__(self, data: bytes):
        self.data = data

    async def read(self, n: int = -1) -> bytes:
        return self.data if n < 0 else self.data[:n]


class ReadCappedTest(unittest.IsolatedAsyncioTestCase):
    async def test_exact_limit_ok_and_over_limit_raises(self):
        self.assertEqual(len(await read_capped(_Upload(b"x" * 10), 10)), 10)
        with self.assertRaises(ValueError):
            await read_capped(_Upload(b"x" * 11), 10)


if __name__ == "__main__":
    unittest.main()
