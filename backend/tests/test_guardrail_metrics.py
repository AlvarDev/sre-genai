import unittest
from types import SimpleNamespace

from agent.guardrail_metrics import VIOLATION_TYPES, token_usage_points

ADK_KEYS = {
    "gen_ai.agent.name",
    "gen_ai.operation.name",
    "gen_ai.provider.name",
    "gen_ai.request.model",
    "gen_ai.response.model",
    "gen_ai.token.type",
}


class TokenPointsTest(unittest.TestCase):
    def test_token_points_match_adk_keys(self):
        um = SimpleNamespace(prompt_token_count=120, candidates_token_count=30, thoughts_token_count=5)
        pts = token_usage_points(um, "gemini-3.5-flash-lite", "gemini-3.5-flash-lite-001")
        self.assertEqual([p[0] for p in pts], [120, 35])
        self.assertEqual(set(pts[0][1]), ADK_KEYS)
        self.assertEqual([p[1]["gen_ai.token.type"] for p in pts], ["input", "output"])
        self.assertEqual(pts[0][1]["gen_ai.agent.name"], "guardrail")
        self.assertEqual(pts[0][1]["gen_ai.operation.name"], "generate_content")
        self.assertEqual(pts[0][1]["gen_ai.provider.name"], "vertex_ai")

    def test_input_includes_tool_use_tokens_like_adk(self):
        um = SimpleNamespace(prompt_token_count=100, tool_use_prompt_token_count=7,
                             candidates_token_count=1, thoughts_token_count=None)
        self.assertEqual([p[0] for p in token_usage_points(um, "m", "m")], [107, 1])

    def test_response_model_falls_back_to_request_model(self):
        um = SimpleNamespace(prompt_token_count=1, candidates_token_count=1, thoughts_token_count=None)
        pts = token_usage_points(um, "m", None)
        self.assertEqual(pts[0][1]["gen_ai.response.model"], "m")

    def test_none_and_zero_skipped(self):
        self.assertEqual(token_usage_points(None, "m", None), [])
        um = SimpleNamespace(prompt_token_count=0, candidates_token_count=None, thoughts_token_count=None)
        self.assertEqual(token_usage_points(um, "m", None), [])

    def test_violation_types(self):
        self.assertEqual(
            VIOLATION_TYPES,
            ("input_jailbreak", "database_drift", "guardrail_system_failure", "guardrail_database_drift_failure"),
        )


if __name__ == "__main__":
    unittest.main()
