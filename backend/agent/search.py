import os
import asyncio
import logging
from urllib.parse import urlparse
import google.auth.transport.requests
from google.oauth2 import id_token
from mcp import ClientSession
from mcp.client.sse import sse_client

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

auth_request = google.auth.transport.requests.Request()


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
            token = id_token.fetch_id_token(auth_request, mcp_audience)
            headers["Authorization"] = f"Bearer {token}"
        except Exception as e:
            logger.error(f"Failed to acquire OIDC token for MCP server: {e}", exc_info=True)
            raise RuntimeError(f"Service authentication failed: unable to obtain OIDC token: {e}") from e
    else:
        # In local dev / local containers: set Host header to 'localhost' to pass
        # the MCP server's default DNS rebinding/host validation check.
        headers["Host"] = "localhost"

    # Inject W3C traceparent header to correlate requests across services
    TraceContextTextMapPropagator().inject(headers)

    return headers

async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """
    Connects to the Catalog MCP Server via SSE, validates the connection,
    invokes the specified tool, and returns the result string.
    """
    headers = get_mcp_headers()
    
    with tracer.start_as_current_span(f"mcp.client.call_tool:{tool_name}") as span:
        span.set_attribute("mcp.tool.name", tool_name)
        span.set_attribute("mcp.server.url", mcp_server_url)
        
        # Establish connection with the MCP SSE transport
        logger.info(f"Connecting to MCP SSE endpoint: {mcp_server_url}")
        async with sse_client(mcp_server_url, headers=headers) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the session handshake
                await session.initialize()
                
                # Invoke the tool
                logger.info(f"Invoking tool: '{tool_name}' with args: {arguments}")
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
    Invokes the search_catalog tool on the Catalog MCP server via SSE transport.
    """
    try:
        return await call_mcp_tool("search_catalog", {"query_text": query_text})
    except Exception as e:
        logger.error(f"Error connecting to catalog search tool: {str(e)}", exc_info=True)
        return f"Error connecting to catalog search tool: {str(e)}"

async def call_catalog_image_search(image_base64: str, mime_type: str = "image/jpeg") -> str:
    """
    Invokes the search_catalog_by_image tool on the Catalog MCP server via SSE transport.
    """
    try:
        return await call_mcp_tool("search_catalog_by_image", {"image_base64": image_base64, "mime_type": mime_type})
    except Exception as e:
        logger.error(f"Error connecting to catalog visual search tool: {str(e)}", exc_info=True)
        return f"Error connecting to catalog visual search tool: {str(e)}"
