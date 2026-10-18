import importlib
import os
import sys
import unittest
from unittest import mock

ENV = {"MCP_SERVER_URL": "https://catalog.example.run.app/mcp/"}


def import_search():
    with mock.patch.dict(os.environ, ENV):
        sys.modules.pop("agent.search", None)
        return importlib.import_module("agent.search")


class SearchClientTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.search = import_search()

    def test_fresh_auth_request_per_call(self):
        # requests.Session isn't documented as thread-safe, and headers are built in
        # worker threads, so each call must use its own transport Request.
        with mock.patch.dict(os.environ, {"K_SERVICE": "backend-gemini"}), \
                mock.patch.object(self.search.google.auth.transport.requests, "Request") as request_cls, \
                mock.patch.object(self.search.id_token, "fetch_id_token", return_value="tok") as fetch:
            self.search.get_mcp_headers()
            self.search.get_mcp_headers()
        self.assertEqual(request_cls.call_count, 2)
        self.assertEqual(fetch.call_args.args[1], "https://catalog.example.run.app")

    def test_no_auth_header_outside_cloud_run(self):
        env = {k: v for k, v in os.environ.items() if k != "K_SERVICE"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertNotIn("Authorization", self.search.get_mcp_headers())

    async def test_http_client_follows_redirects(self):
        http = self.search.build_mcp_http_client({"x-test": "1"})
        try:
            self.assertTrue(http.follow_redirects)
            self.assertEqual(http.headers["x-test"], "1")
        finally:
            await http.aclose()

    def test_catalog_error_message_is_shared(self):
        from agent.catalog_messages import CATALOG_ERROR_MESSAGE
        self.assertEqual(self.search.CATALOG_ERROR_MESSAGE, CATALOG_ERROR_MESSAGE)
        self.assertEqual(CATALOG_ERROR_MESSAGE, "Erro ao consultar o catálogo.")


if __name__ == "__main__":
    unittest.main()
