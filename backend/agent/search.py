import os
import asyncio
import logging
from urllib.parse import urlparse
import google.auth.transport.requests
from google.oauth2 import id_token
from mcp import ClientSession
from mcp.client.sse import sse_client

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mcp-client")

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

    return headers

async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """
    Connects to the Catalog MCP Server via SSE, validates the connection,
    invokes the specified tool, and returns the result string.
    """
    headers = get_mcp_headers()
    
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

async def search_catalog_tool(query_text: str) -> str:
    """
    Wraps the async call to search_catalog for the ADK agent engine.
    """
    try:
        return await call_mcp_tool("search_catalog", {"query_text": query_text})
    except Exception as e:
        logger.error(f"Error connecting to catalog search tool: {str(e)}", exc_info=True)
        return f"Error connecting to catalog search tool: {str(e)}"

async def search_catalog_by_image_tool(image_vector: list[float]) -> str:
    """
    Wraps the async call to search_catalog_by_image for the ADK agent engine.
    """
    try:
        return await call_mcp_tool("search_catalog_by_image", {"image_vector": image_vector})
    except Exception as e:
        logger.error(f"Error connecting to catalog visual search tool: {str(e)}", exc_info=True)
        return f"Error connecting to catalog visual search tool: {str(e)}"
