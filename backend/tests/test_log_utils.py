import unittest

from agent.log_utils import summarize_tool_args


class SummarizeToolArgsTest(unittest.TestCase):
    def test_long_string_is_replaced(self):
        out = summarize_tool_args({"image_base64": "A" * 5000, "mime_type": "image/png"})
        self.assertEqual(out, {"image_base64": "<str len=5000>", "mime_type": "image/png"})

    def test_short_values_kept(self):
        self.assertEqual(summarize_tool_args({"query_text": "pixel 9"}), {"query_text": "pixel 9"})

    def test_boundary_256_kept_257_replaced(self):
        self.assertEqual(summarize_tool_args({"q": "x" * 256})["q"], "x" * 256)
        self.assertEqual(summarize_tool_args({"q": "x" * 257})["q"], "<str len=257>")

    def test_input_not_mutated(self):
        args = {"q": "x" * 300}
        summarize_tool_args(args)
        self.assertEqual(len(args["q"]), 300)


if __name__ == "__main__":
    unittest.main()
