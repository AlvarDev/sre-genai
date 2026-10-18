import importlib
import os
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

ENV = {"PROJECT_ID": "test-project", "GEMINI_LOCATION": "us"}


def import_guardrail():
    """Imports agent.guardrail with the GenAI client patched out (no cloud calls)."""
    with mock.patch.dict(os.environ, ENV), mock.patch("google.genai.Client"):
        sys.modules.pop("agent.guardrail", None)
        return importlib.import_module("agent.guardrail")


def fake_response(text, finish_reason):
    return SimpleNamespace(
        text=text,
        usage_metadata=None,
        model_version=None,
        candidates=[SimpleNamespace(finish_reason=finish_reason)],
    )


class GuardrailFlowTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.guardrail = import_guardrail()
        from agent.catalog_messages import CATALOG_ERROR_MESSAGE
        cls.catalog_error = CATALOG_ERROR_MESSAGE

    def setUp(self):
        self.generate = mock.AsyncMock()
        self.guardrail.client = SimpleNamespace(
            aio=SimpleNamespace(models=SimpleNamespace(generate_content=self.generate))
        )

    async def test_catalog_error_skips_drift_audit(self):
        # The catalog error (from the client or from a catalog-mcp tool failure) must not
        # be sent to the drift auditor: no LLM call, and the message passes through.
        result = await self.guardrail.filter_retrieved_products(self.catalog_error)
        self.assertEqual(result, self.catalog_error)
        self.generate.assert_not_called()

    async def test_truncated_input_check_logs_finish_reason(self):
        self.generate.return_value = fake_response('{"is_sa', "MAX_TOKENS")
        with self.assertLogs("guardrail", level="ERROR") as logs:
            with self.assertRaises(self.guardrail.GuardrailException):
                await self.guardrail.validate_user_input("oi")
        self.assertIn("MAX_TOKENS", "\n".join(logs.output))

    async def test_truncated_drift_audit_logs_finish_reason(self):
        self.generate.return_value = fake_response('{"evaluations": [', "MAX_TOKENS")
        with self.assertLogs("guardrail", level="ERROR") as logs:
            result = await self.guardrail.filter_retrieved_products("Title: Pixel\nSKU: P1\n")
        self.assertEqual(result, "Não foi possível verificar a integridade dos produtos no momento.")
        self.assertIn("MAX_TOKENS", "\n".join(logs.output))

    def test_output_caps(self):
        self.assertEqual(self.guardrail.INPUT_CHECK_MAX_OUTPUT_TOKENS, 512)
        self.assertEqual(self.guardrail.DRIFT_AUDIT_MAX_OUTPUT_TOKENS, 1024)


if __name__ == "__main__":
    unittest.main()
