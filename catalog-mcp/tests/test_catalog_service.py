import asyncio
import time
import unittest
from types import SimpleNamespace

from catalog_service import EMBEDDING_DIM, EMBEDDING_MODEL, search_by_image, search_by_text
from repository import ProductCatalogRepository


class FakeModels:
    """Records embed_content calls and simulates network latency."""

    def __init__(self):
        self.calls = []

    async def embed_content(self, model, contents, config):
        self.calls.append((model, config.output_dimensionality))
        await asyncio.sleep(0.2)
        return SimpleNamespace(embeddings=[SimpleNamespace(values=[0.1] * 768)])


class FakeRepo:
    async def find_similar_products(self, vector, limit=3):
        return [{"title": "Pixel", "parent_sku": "P1"}]

    format_products_to_string = staticmethod(ProductCatalogRepository.format_products_to_string)


class CatalogServiceTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.models = FakeModels()
        self.client = SimpleNamespace(aio=SimpleNamespace(models=self.models))

    async def test_text_uses_model_and_dim(self):
        text, n = await search_by_text(self.client, FakeRepo(), "pixel")
        self.assertEqual(self.models.calls, [("gemini-embedding-2", 768)])
        self.assertEqual((EMBEDDING_MODEL, EMBEDDING_DIM), ("gemini-embedding-2", 768))
        self.assertEqual(n, 1)
        self.assertIn("SKU: P1", text)

    async def test_image(self):
        _, n = await search_by_image(self.client, FakeRepo(), b"\xff\xd8\xff", "image/jpeg")
        self.assertEqual(n, 1)
        self.assertEqual(self.models.calls, [("gemini-embedding-2", 768)])

    async def test_concurrent_calls_do_not_block(self):
        t0 = time.perf_counter()
        await asyncio.gather(*(search_by_text(self.client, FakeRepo(), "q") for _ in range(5)))
        self.assertLess(time.perf_counter() - t0, 0.6)


if __name__ == "__main__":
    unittest.main()
