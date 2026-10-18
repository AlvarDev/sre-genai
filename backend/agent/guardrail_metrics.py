"""Pure helpers for guardrail telemetry (no OpenTelemetry/GenAI imports, unit-testable).

Token points mirror ADK 2.4.0 ``google.adk.telemetry._metrics.record_client_token_usage``
so guardrail calls land in the same ``gen_ai.client.token.usage`` metric with the same
label keys as the main agent's calls.
"""

VIOLATION_TYPES: tuple[str, ...] = (
    "input_jailbreak",
    "database_drift",
    "guardrail_system_failure",
    "guardrail_database_drift_failure",
)

GUARDRAIL_AGENT_NAME = "guardrail"
# The guardrail's genai.Client is created with vertexai=True.
PROVIDER_NAME = "vertex_ai"


def token_usage_points(usage_metadata, request_model: str, response_model: str | None) -> list[tuple[int, dict]]:
    """Returns ``[(token_count, attributes), ...]`` for input and output tokens.

    Input = prompt + tool-use prompt tokens; output = candidates + thoughts tokens
    (same as ADK). Zero or missing counts produce no point.
    """
    if usage_metadata is None:
        return []

    input_tokens = (getattr(usage_metadata, "prompt_token_count", None) or 0) + (
        getattr(usage_metadata, "tool_use_prompt_token_count", None) or 0
    )
    output_tokens = (getattr(usage_metadata, "candidates_token_count", None) or 0) + (
        getattr(usage_metadata, "thoughts_token_count", None) or 0
    )

    base_attrs = {
        "gen_ai.agent.name": GUARDRAIL_AGENT_NAME,
        "gen_ai.operation.name": "generate_content",
        "gen_ai.provider.name": PROVIDER_NAME,
    }
    if request_model:
        base_attrs["gen_ai.request.model"] = request_model
    effective_response_model = response_model or request_model
    if effective_response_model:
        base_attrs["gen_ai.response.model"] = effective_response_model

    points = []
    if input_tokens > 0:
        points.append((input_tokens, {**base_attrs, "gen_ai.token.type": "input"}))
    if output_tokens > 0:
        points.append((output_tokens, {**base_attrs, "gen_ai.token.type": "output"}))
    return points
