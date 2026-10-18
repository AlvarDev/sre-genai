import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from cors import add_cors, parse_allowed_origins


class ParseOriginsTest(unittest.TestCase):
    def test_parses_and_strips(self):
        self.assertEqual(
            parse_allowed_origins(" https://a.app , http://localhost:3000 "),
            ["https://a.app", "http://localhost:3000"],
        )

    def test_missing_or_empty_raises(self):
        for raw in (None, "", " , "):
            with self.assertRaises(RuntimeError):
                parse_allowed_origins(raw)

    def test_wildcard_rejected(self):
        with self.assertRaises(RuntimeError):
            parse_allowed_origins("https://a.app,*")


class CorsPreflightTest(unittest.TestCase):
    def test_cors_preflight(self):
        app = FastAPI()
        add_cors(app, ["https://a.app"])

        @app.post("/chat")
        def chat():
            return {}

        client = TestClient(app)
        ok = client.options(
            "/chat",
            headers={
                "Origin": "https://a.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.headers.get("access-control-allow-origin"), "https://a.app")

        bad = client.options(
            "/chat",
            headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
        )
        self.assertNotIn("access-control-allow-origin", bad.headers)


if __name__ == "__main__":
    unittest.main()
