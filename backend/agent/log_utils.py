"""Helpers to keep large or sensitive tool payloads out of logs."""


def summarize_tool_args(arguments: dict, max_len: int = 256) -> dict:
    """Returns a copy of ``arguments`` that is safe to log.

    String values longer than ``max_len`` (e.g. base64-encoded images) are
    replaced by ``"<str len=N>"`` so they never reach Cloud Logging.
    """
    return {
        key: f"<str len={len(value)}>" if isinstance(value, str) and len(value) > max_len else value
        for key, value in arguments.items()
    }
