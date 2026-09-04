import os
import asyncio
import logging
import time
import threading
from mcp import ClientSession
from mcp.client.sse import sse_client

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mcp-client")

# Get MCP Server URL from environment
mcp_server_url = os.getenv("MCP_SERVER_URL")
if not mcp_server_url:
    raise RuntimeError("MCP_SERVER_URL environment variable is required but not set.")


class OIDCTokenCache:
    """
    Thread-safe cache for Google OIDC Identity Tokens.
    Avoids making blocking network calls to GCP's metadata server on every request.
    """
    def __init__(self, audience: str, cache_duration_seconds: int = 3000):
        self.audience = audience
        self.cache_duration = cache_duration_seconds
        self._token = None
        self._expiry = 0
        self._lock = threading.Lock()

    def get_token(self) -> str:
        now = time.time()
        
        # 1. Check cache (thread-safe)
        with self._lock:
            if self._token and now < self._expiry:
                return self._token
        
        # 2. Cache miss/expired: Fetch fresh token
        import requests
        metadata_url = (
            "http://metadata.google.internal/computeMetadata/v1/instance/"
            f"service-accounts/default/identity?audience={self.audience}"
        )
        try:
            logger.info("OIDC token cache miss/expired. Fetching fresh token from GCP metadata server...")
            response = requests.get(metadata_url, headers={"Metadata-Flavor": "Google"}, timeout=2)
            token = response.text.strip()
            
            # 3. Save to cache (thread-safe)
            with self._lock:
                self._token = token
                self._expiry = time.time() + self.cache_duration
            return token
        except Exception as e:
            logger.error(f"Failed to fetch OIDC token from metadata server: {e}", exc_info=True)
            raise e


# Initialize the token cache globally for the target MCP server URL
token_cache = OIDCTokenCache(audience=mcp_server_url)


def get_mcp_headers() -> dict:
    """
    Generates authentication headers for the MCP call.
    Uses OIDC identity token in production (Cloud Run) and bypasses in local dev.
    """
    headers = {}
    
    # Check if running in Google Cloud Run (sets K_SERVICE automatically)
    if os.getenv("K_SERVICE"):
        try:
            token = token_cache.get_token()
            headers["Authorization"] = f"Bearer {token}"
        except Exception:
            # Error has already been caught and logged inside the token cache
            pass
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
