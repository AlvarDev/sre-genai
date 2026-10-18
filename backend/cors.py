"""Strict CORS configuration driven by the ALLOWED_ORIGINS env var."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def parse_allowed_origins(raw: str | None) -> list[str]:
    """Parses a comma-separated origin list.

    Fails fast (RuntimeError) when the list is missing/empty or contains "*",
    so a misconfigured deploy never silently allows every origin.
    """
    origins = [origin.strip() for origin in (raw or "").split(",") if origin.strip()]
    if not origins:
        raise RuntimeError("ALLOWED_ORIGINS environment variable is required but not set.")
    if "*" in origins:
        raise RuntimeError("ALLOWED_ORIGINS must list explicit origins; '*' is not allowed.")
    return origins


def add_cors(app: FastAPI, origins: list[str]) -> None:
    """Allows only the given origins, the methods and headers the frontend uses."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )
