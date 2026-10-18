import importlib
import os
import sys
import unittest
from unittest import mock

from opentelemetry import trace

ENV = {
    "PROJECT_ID": "test-project",
    "GEMINI_LOCATION": "us",
    "FIRESTORE_DATABASE": "test-db",
    "SERVICE_NAME": "catalog-mcp-test",
}


def import_main_without_cloud():
    """Imports main.py with cloud clients and exporters patched out (local, non-prod mode)."""
    env = {k: v for k, v in os.environ.items() if k not in ("K_SERVICE", "KUBERNETES_SERVICE_HOST")}
    env.update(ENV)
    with mock.patch.dict(os.environ, env, clear=True), \
            mock.patch("google.cloud.firestore.AsyncClient"), \
            mock.patch("google.genai.Client"), \
            mock.patch("telemetry.setup_telemetry", return_value=(None, trace.get_tracer("test"))):
        sys.modules.pop("main", None)
        return importlib.import_module("main")


class MainSettingsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = import_main_without_cloud()

    def test_stateless_settings(self):
        settings = self.main.mcp.settings
        self.assertTrue(settings.stateless_http)
        self.assertTrue(settings.json_response)
        self.assertEqual(settings.streamable_http_path, "/")
        self.assertIn("/mcp", [getattr(route, "path", None) for route in self.main.app.routes])

    def test_local_mode_allows_localhost_hosts(self):
        security = self.main.mcp.settings.transport_security
        self.assertTrue(security.enable_dns_rebinding_protection)
        self.assertEqual(security.allowed_hosts, ["localhost:*", "127.0.0.1:*"])


class ToolErrorTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = import_main_without_cloud()

    async def test_tool_errors_are_generic(self):
        boom = mock.AsyncMock(side_effect=RuntimeError("secret internal detail"))
        with mock.patch.object(self.main.catalog_service, "search_by_text", boom):
            self.assertEqual(await self.main.search_catalog("x"), "Erro ao consultar o catálogo.")
        with mock.patch.object(self.main.catalog_service, "search_by_image", boom):
            self.assertEqual(await self.main.search_catalog_by_image("/9j/"), "Erro ao consultar o catálogo.")


if __name__ == "__main__":
    unittest.main()
