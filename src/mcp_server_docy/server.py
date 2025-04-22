from typing import Annotated, Dict, List, Optional
import json
import httpx
import asyncio
import time
from cachetools import TTLCache
from functools import wraps
from loguru import logger
from mcp.shared.exceptions import McpError
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    ErrorData,
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler

# Remove default handler to allow configuration from __main__.py
logger.remove()

# Server metadata
SERVER_NAME = "Docy"
SERVER_VERSION = "0.1.0"
DEFAULT_USER_AGENT = f"ModelContextProtocol/1.0 {SERVER_NAME} (+https://github.com/modelcontextprotocol/servers)"

# HTTP request cache (default ttl=1 hour, configurable)
_http_cache = None  # Will be initialized in serve()
_cache_lock = asyncio.Lock()

# Store for documentation URLs (populated at startup)
DOCUMENTATION_URLS = []


def async_cached(cache):
    """Decorator to cache results of async functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create a cache key from the function name and arguments
            key = str(args) + str(kwargs)
            
            # Check if the result is already in the cache
            if cache and key in cache:
                logger.info(f"Cache HIT for {func.__name__}")
                return cache[key]
                
            logger.info(f"Cache MISS for {func.__name__}")
            
            # Call the original function
            try:
                result = await func(*args, **kwargs)
                
                # Update the cache with the result (with lock to avoid race conditions)
                if cache:
                    async with _cache_lock:
                        cache[key] = result
                
                return result
            except Exception as e:
                logger.error(f"Error executing {func.__name__}: {str(e)}")
                raise
                
        return wrapper
    return decorator


class DocumentationUrl(BaseModel):
    """Parameters for accessing a documentation page by URL."""
    url: Annotated[
        str,
        Field(description="The URL of the documentation page to access"),
    ]


@async_cached(_http_cache)
async def fetch_documentation_content(url: str) -> Dict:
    """Fetch the content of a documentation page by direct URL."""
    logger.info(f"Fetching documentation page content from {url}")
    
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            
            # Return information about the documentation page
            return {
                "url": url,
                "title": result.title,
                "markdown": result.markdown,
                "links": result.links,
            }
    except Exception as e:
        logger.error(f"Failed to fetch documentation page content from {url}: {str(e)}")
        raise McpError(
            ErrorData(
                code=INTERNAL_ERROR,
                message=f"Failed to fetch documentation content: {str(e)}",
            )
        )


def list_documentation_sources() -> List[Dict]:
    """List all configured documentation sources."""
    logger.info(f"Listing all {len(DOCUMENTATION_URLS)} documentation sources")
    
    results = []
    for url in DOCUMENTATION_URLS:
        results.append({
            "url": url,
            "type": "web",
            "description": "Web-based documentation"
        })
    
    return results


async def serve(
    custom_user_agent: str | None = None,
    documentation_urls: List[str] | None = None,
    cache_ttl: int = 3600,
) -> None:
    """Run the documentation MCP server.

    Args:
        custom_user_agent: Optional custom User-Agent string to use for requests
        documentation_urls: List of documentation site URLs to include
        cache_ttl: Cache time-to-live in seconds (default: 3600)
    """
    logger.info("Starting mcp-docy server")

    global DEFAULT_USER_AGENT, DOCUMENTATION_URLS, _http_cache
    
    # Initialize cache with provided TTL
    _http_cache = TTLCache(maxsize=500, ttl=cache_ttl)
    logger.info(f"Initialized HTTP cache with TTL: {cache_ttl}s")
    
    if custom_user_agent:
        logger.info(f"Using custom User-Agent: {custom_user_agent}")
        DEFAULT_USER_AGENT = custom_user_agent
    
    # Store documentation URLs
    if documentation_urls:
        DOCUMENTATION_URLS = documentation_urls
        logger.info(f"Configured {len(DOCUMENTATION_URLS)} documentation sources")
    else:
        logger.warning("No documentation URLs provided. The server will have no content to serve.")
        DOCUMENTATION_URLS = []

    server = Server("mcp-docy")
    logger.info("MCP Server initialized")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="list_documentation_sources",
                description="""List all available documentation sources this service has access to.
                
This tool requires no input parameters and returns a list of documentation sources configured for this service.
Use this tool first to discover what documentation sources are available.

Example usage:
```
list_documentation_sources()
```

Response provides the URLs to documentation sources and their types.""",
                inputSchema={},  # No input needed
            ),
            Tool(
                name="fetch_documentation_page",
                description="""Fetch the content of a documentation page by URL as markdown.
                
This tool retrieves the full content from a documentation page at the specified URL and returns it as markdown.
The markdown format preserves headings, links, lists, and other formatting from the original documentation.

Example usage:
```
fetch_documentation_page(url="https://example.com/documentation/page")
```

Response includes the full markdown content of the page along with metadata like title and links.""",
                inputSchema=DocumentationUrl.model_json_schema(),
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        logger.info(f"Tool call: {name} with arguments: {arguments}")

        if name == "list_documentation_sources":
            logger.info("Listing documentation sources")
            results = list_documentation_sources()
            logger.info(f"Found {len(results)} documentation sources")
            return [
                TextContent(
                    type="text",
                    text=f"Available documentation sources:\n{json.dumps(results, indent=2)}",
                )
            ]

        elif name == "fetch_documentation_page":
            try:
                args = DocumentationUrl(**arguments)
                logger.debug(f"Validated documentation URL args: {args}")
            except ValueError as e:
                logger.error(f"Invalid documentation URL parameters: {str(e)}")
                raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))

            logger.info(f"Fetching documentation page content for URL: {args.url}")
            result = await fetch_documentation_content(args.url)
            logger.info(f"Successfully fetched documentation page content")
            return [
                TextContent(
                    type="text",
                    text=f"# {result['title']}\n\n{result['markdown']}",
                )
            ]

        logger.error(f"Unknown tool: {name}")
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Unknown tool: {name}"))

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        return [
            Prompt(
                name="list_documentation_sources",
                description="List all available documentation sources with their URLs and types",
                arguments=[],  # No arguments needed
            ),
            Prompt(
                name="fetch_documentation_page",
                description="Fetch the full content of a documentation page at a specific URL as markdown",
                arguments=[
                    PromptArgument(
                        name="url",
                        description="The complete URL of the documentation page to access",
                        required=True,
                    )
                ],
            ),
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None) -> GetPromptResult:
        logger.info(f"Prompt request: {name} with arguments: {arguments}")

        if name == "list_documentation_sources":
            logger.info("Getting list_documentation_sources prompt")
            try:
                results = list_documentation_sources()
                logger.info(f"Found {len(results)} documentation sources")
                return GetPromptResult(
                    description="List of available documentation sources",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(
                                type="text",
                                text=f"Available documentation sources:\n{json.dumps(results, indent=2)}",
                            ),
                        )
                    ],
                )
            except McpError as e:
                logger.error(f"Error generating list_documentation_sources prompt: {str(e)}")
                return GetPromptResult(
                    description="Failed to list documentation sources",
                    messages=[
                        PromptMessage(
                            role="user", content=TextContent(type="text", text=str(e))
                        )
                    ],
                )

        elif name == "fetch_documentation_page":
            if not arguments or "url" not in arguments:
                logger.error("Missing required 'url' parameter for fetch_documentation_page prompt")
                raise McpError(
                    ErrorData(code=INVALID_PARAMS, message="Documentation page URL is required")
                )
                
            url = arguments["url"]
            logger.info(f"Fetching documentation page content for URL: {url}")

            try:
                result = await fetch_documentation_content(url)
                logger.info(f"Successfully fetched content for URL: {url}")
                return GetPromptResult(
                    description=f"Documentation content for {result['title']}",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(
                                type="text",
                                text=f"# {result['title']}\n\n{result['markdown']}",
                            ),
                        )
                    ],
                )
            except McpError as e:
                logger.error(f"Error generating fetch_documentation_page prompt: {str(e)}")
                return GetPromptResult(
                    description=f"Failed to fetch content from URL: {url}",
                    messages=[
                        PromptMessage(
                            role="user", content=TextContent(type="text", text=str(e))
                        )
                    ],
                )

        raise McpError(
            ErrorData(code=INVALID_PARAMS, message=f"Unknown prompt: {name}")
        )

    options = server.create_initialization_options()
    logger.info("Starting server with stdio transport")
    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Server ready to accept connections")
            await server.run(read_stream, write_stream, options, raise_exceptions=True)
    except Exception as e:
        logger.error(f"Server encountered an error: {str(e)}")
        raise
    finally:
        logger.info("Server shutdown complete")