import os
import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

# Get MCP Server URL from environment (default to local dev URL)
# The SSE endpoint is mounted at /mcp/sse in the FastAPI server
mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001/mcp/sse")

def get_mcp_headers() -> dict:
    """
    Generates authentication headers for the MCP call.
    Uses OIDC identity token in production (Cloud Run) and bypasses in local dev.
    """
    headers = {}
    
    # Check if running in Google Cloud Run (sets K_SERVICE automatically)
    if os.getenv("K_SERVICE"):
        # In production Cloud Run: query the metadata server for OIDC token
        import requests
        metadata_url = (
            "http://metadata.google.internal/computeMetadata/v1/instance/"
            f"service-accounts/default/identity?audience={mcp_server_url}"
        )
        try:
            response = requests.get(metadata_url, headers={"Metadata-Flavor": "Google"}, timeout=2)
            oidc_token = response.text
            headers["Authorization"] = f"Bearer {oidc_token}"
        except Exception as e:
            print(f"Error fetching OIDC Token: {e}")
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
    async with sse_client(mcp_server_url, headers=headers) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the session handshake
            await session.initialize()
            
            # Invoke the tool
            result = await session.call_tool(tool_name, arguments=arguments)
            
            # Extract content from result
            if hasattr(result, "content") and result.content:
                text_contents = [c.text for c in result.content if hasattr(c, "text")]
                return "\n".join(text_contents)
            return "No data returned from catalog tool."

from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=4)

def run_sync(coro):
    """
    Helper to run a coroutine synchronously by offloading it to a background thread
    with a fresh event loop (using asyncio.run), bypassing the main running event loop.
    """
    return _executor.submit(asyncio.run, coro).result()

def search_catalog_tool(query_text: str) -> str:
    """
    Wraps the async call to search_catalog for the ADK agent engine.
    """
    try:
        return run_sync(call_mcp_tool("search_catalog", {"query_text": query_text}))
    except Exception as e:
        return f"Error connecting to catalog search tool: {str(e)}"

def search_catalog_by_image_tool(image_vector: list[float]) -> str:
    """
    Wraps the async call to search_catalog_by_image for the ADK agent engine.
    """
    try:
        return run_sync(call_mcp_tool("search_catalog_by_image", {"image_vector": image_vector}))
    except Exception as e:
        return f"Error connecting to catalog visual search tool: {str(e)}"
