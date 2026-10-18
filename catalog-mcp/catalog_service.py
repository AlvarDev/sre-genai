"""Async catalog search: embeds the query with Gemini and runs a Firestore vector search.

Kept free of MCP/FastAPI concerns so it can be unit-tested with fakes.
"""
from google.genai import types

EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIM = 768


async def _embed(genai_client, contents) -> list[float]:
    result = await genai_client.aio.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=contents,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
    )
    return result.embeddings[0].values


async def _search(repo, vector: list[float]) -> tuple[str, int]:
    products = await repo.find_similar_products(vector)
    return repo.format_products_to_string(products), len(products)


async def search_by_text(genai_client, repo, query_text: str) -> tuple[str, int]:
    """Returns (formatted products, result count) for a natural language query."""
    vector = await _embed(genai_client, query_text)
    return await _search(repo, vector)


async def search_by_image(genai_client, repo, image_bytes: bytes, mime_type: str) -> tuple[str, int]:
    """Returns (formatted products, result count) for an image query."""
    vector = await _embed(
        genai_client, [types.Part.from_bytes(data=image_bytes, mime_type=mime_type)]
    )
    return await _search(repo, vector)
