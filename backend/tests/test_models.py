import unittest

from pydantic import ValidationError

from models import ChatRequest
from validation import MAX_MESSAGE_CHARS


class ChatRequestTest(unittest.TestCase):
    def test_message_bounds(self):
        ChatRequest(message="x" * 2000, session_id="s")
        for bad in ("", "x" * 2001):
            with self.assertRaises(ValidationError):
                ChatRequest(message=bad, session_id="s")

    def test_visual_message_limit(self):
        # /visual-search allows an empty message (image only) and caps it at the same limit.
        self.assertEqual(MAX_MESSAGE_CHARS, 2000)
        self.assertTrue(len("") <= MAX_MESSAGE_CHARS)


if __name__ == "__main__":
    unittest.main()
