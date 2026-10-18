import os
import asyncio
import logging
from urllib.parse import urlparse
import httpx  # provided by the mcp SDK (dependency of its HTTP transports)
import google.auth.transport.requests
from google.oauth2 import id_token
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from agent.catalog_messages import CATALOG_ERROR_MESSAGE
from agent.log_utils import summarize_tool_args

# Configure logging
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger("mcp-client")
tracer = trace.get_tracer("backend.mcp-client")

# Get MCP Server URL from environment
mcp_server_url = os.getenv("MCP_SERVER_URL")
if not mcp_server_url:
    raise RuntimeError("MCP_SERVER_URL environment variable is required but not set.")

# Cloud Run uses the target service hostname as audience
parsed_url = urlparse(mcp_server_url)
mcp_audience = f"{parsed_url.scheme}://{parsed_url.netloc}"


def get_mcp_headers() -> dict:
    """
    Generates authentication headers for the MCP call.
    Uses OIDC identity token in production (Cloud Run) and bypasses in local dev.
    Injects W3C traceparent context into headers for distributed tracing.
    """
    headers = {}
    
    # Check if running in Google Cloud Run (sets K_SERVICE automatically)
    if os.getenv("K_SERVICE"):
        try:
            # A fresh transport per call: this runs in worker threads, and the
            # requests.Session behind Request() isn't documented as thread-safe.
            auth_request = google.auth.transport.requests.Request()
            token = id_token.fetch_id_token(auth_request, mcp_audience)
            headers["Authorization"] = f"Bearer {token}"
        except Exception as e:
            logger.error(f"Failed to acquire OIDC token for MCP server: {e}", exc_info=True)
            raise RuntimeError(f"Service authentication failed: unable to obtain OIDC token: {e}") from e

    # Inject W3C traceparent header to correlate requests across services
    TraceContextTextMapPropagator().inject(headers)

    return headers

# Connect fast; allow slow tool calls (embedding + vector search) to finish.
# Note: on Cloud Run the catalog-mcp request timeout (--timeout=30s in
# catalog-mcp/cloudbuild.yaml) is the effective limit, not this read timeout.
MCP_HTTP_TIMEOUT = httpx.Timeout(30.0, read=300.0)

def build_mcp_http_client(headers: dict) -> httpx.AsyncClient:
    """HTTP client for one MCP call. Follows redirects like the MCP SDK's default client
    (e.g. a MCP_SERVER_URL without the trailing slash gets a 307 to /mcp/)."""
    return httpx.AsyncClient(headers=headers, timeout=MCP_HTTP_TIMEOUT, follow_redirects=True)

async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """
    Connects to the Catalog MCP Server via stateless Streamable HTTP,
    invokes the specified tool, and returns the result string.
    """
    with tracer.start_as_current_span(f"mcp.client.call_tool:{tool_name}") as span:
        span.set_attribute("mcp.tool.name", tool_name)
        span.set_attribute("mcp.server.url", mcp_server_url)

        # Built inside the span so traceparent points at it. fetch_id_token is blocking,
        # so run it in a worker thread (to_thread keeps the current trace context).
        headers = await asyncio.to_thread(get_mcp_headers)

        logger.info(f"Connecting to MCP Streamable HTTP endpoint: {mcp_server_url}")
        async with build_mcp_http_client(headers) as http:
            async with streamable_http_client(mcp_server_url, http_client=http) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    # Initialize the session handshake
                    await session.initialize()

                    # Invoke the tool
                    logger.info(f"Invoking tool: '{tool_name}' with args: {summarize_tool_args(arguments)}")
                    result = await session.call_tool(tool_name, arguments=arguments)

                    # Extract content from result
                    if hasattr(result, "content") and result.content:
                        text_contents = [c.text for c in result.content if hasattr(c, "text")]
                        logger.info(f"Successfully received response from tool '{tool_name}'.")
                        return "\n".join(text_contents)

                    logger.warning(f"Tool '{tool_name}' returned empty or null content.")
                    return "No data returned from catalog tool."

async def call_catalog_text_search(query_text: str) -> str:
    """
    Invokes the search_catalog tool on the Catalog MCP server.
    """
    try:
        return await call_mcp_tool("search_catalog", {"query_text": query_text})
    except Exception:
        logger.exception("Error connecting to catalog search tool")
        return CATALOG_ERROR_MESSAGE

async def call_catalog_image_search(image_base64: str, mime_type: str = "image/jpeg") -> str:
    """
    Invokes the search_catalog_by_image tool on the Catalog MCP server.
    """
    try:
        return await call_mcp_tool("search_catalog_by_image", {"image_base64": image_base64, "mime_type": mime_type})
    except Exception:
        logger.exception("Error connecting to catalog visual search tool")
        return CATALOG_ERROR_MESSAGE
