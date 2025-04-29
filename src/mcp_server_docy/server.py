from typing import Dict, List, Literal, Optional
import json
import os
import subprocess
import asyncio
from functools import wraps
from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from fastmcp import FastMCP
from crawl4ai import AsyncWebCrawler
from diskcache import Cache

# Remove default handler to allow configuration from __main__.py
logger.remove()

# Server metadata
SERVER_NAME = "Docy"
SERVER_VERSION = "0.5.0"
DEFAULT_USER_AGENT = f"ModelContextProtocol/1.0 {SERVER_NAME} (+https://github.com/modelcontextprotocol/servers)"


class Settings(BaseSettings):
    """Configuration settings for the Docy server."""

    model_config = SettingsConfigDict(extra="ignore", env_file=".env")

    docy_user_agent: str = Field(
        default=DEFAULT_USER_AGENT,
        description="Custom User-Agent string for HTTP requests",
    )
    docy_documentation_urls: Optional[str] = Field(
        default=None,
        description="Comma-separated list of URLs to documentation sites to include",
    )
    docy_documentation_urls_file: Optional[str] = Field(
        default=".docy.urls",
        description="Path to a file containing documentation URLs (one per line)",
    )
    docy_cache_ttl: int = Field(
        default=432000, description="Cache time-to-live in seconds"
    )
    docy_cache_directory: str = Field(
        default=".docy.cache", description="Path to the cache directory"
    )
    docy_debug: bool = Field(default=False, description="Enable debug logging")
    docy_skip_crawl4ai_setup: bool = Field(
        default=False, description="Skip running crawl4ai-setup command at startup"
    )
    docy_transport: Literal["sse", "stdio"] = Field(
        default="stdio", description="Transport protocol (sse or stdio)"
    )
    docy_host: str = Field(
        default="127.0.0.1", description="Host address to bind the server to"
    )
    docy_port: int = Field(default=8000, description="Port to run the server on")

    @property
    def user_agent(self) -> str:
        return self.docy_user_agent

    @property
    def cache_ttl(self) -> int:
        return self.docy_cache_ttl

    @property
    def cache_directory(self) -> str:
        return self.docy_cache_directory

    @property
    def debug(self) -> bool:
        return self.docy_debug

    @property
    def skip_crawl4ai_setup(self) -> bool:
        return self.docy_skip_crawl4ai_setup

    @property
    def documentation_urls_str(self) -> Optional[str]:
        return self.docy_documentation_urls

    @property
    def documentation_urls_file_path(self) -> Optional[str]:
        return self.docy_documentation_urls_file

    @property
    def transport(self) -> Literal["sse", "stdio"]:
        return self.docy_transport

    @property
    def host(self) -> str:
        return self.docy_host

    @property
    def port(self) -> int:
        return self.docy_port

    def _read_urls_from_file(self) -> List[str]:
        """Read URLs from a file, one per line."""
        import os

        if not self.documentation_urls_file_path:
            return []

        try:
            if not os.path.exists(self.documentation_urls_file_path):
                logger.debug(
                    f"URLs file not found: {self.documentation_urls_file_path}"
                )
                return []

            with open(self.documentation_urls_file_path, "r") as f:
                lines = f.readlines()

            # Filter out empty lines and comments, strip whitespace
            urls = [
                line.strip()
                for line in lines
                if line.strip() and not line.strip().startswith("#")
            ]

            logger.debug(
                f"Read {len(urls)} URLs from file: {self.documentation_urls_file_path}"
            )
            return urls

        except Exception as e:
            logger.error(
                f"Error reading URLs file {self.documentation_urls_file_path}: {str(e)}"
            )
            return []

    @property
    def documentation_urls(self) -> List[str]:
        """Parse the comma-separated URLs into a list, or read from file if no env var provided."""
        # Add debug output to help diagnose environment variable issues
        logger.debug(f"Documentation URLs string: '{self.documentation_urls_str}'")

        # First try to get URLs from environment variable
        if self.documentation_urls_str:
            # Split by comma and strip whitespace from each URL
            urls = [
                url.strip()
                for url in self.documentation_urls_str.split(",")
                if url.strip()
            ]
            logger.debug(
                f"Parsed {len(urls)} documentation URLs from environment variable: {urls}"
            )
            return urls

        # If no URLs in env var, try to read from file
        urls = self._read_urls_from_file()
        if urls:
            return urls

        # No URLs found anywhere
        logger.warning(
            "No documentation URLs provided (neither via environment variable nor file)"
        )
        return []


settings = Settings()

# Cache for HTTP requests (will be initialized in create_server)
cache = None


def async_cached(func):
    """Decorator to cache results of async functions using diskcache.

    Uses an executor to prevent blocking the event loop during cache operations.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        global cache
        loop = asyncio.get_event_loop()

        if cache is None:
            logger.warning("Cache not initialized, skipping caching")
            return await func(*args, **kwargs)

        # Create a cache key from the function name and arguments
        key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

        # Try to get the result from cache (offload to executor)
        cached_result = await loop.run_in_executor(None, lambda: cache.get(key))

        if cached_result is not None:
            logger.info(f"Cache HIT for {func.__name__}")
            return cached_result

        logger.info(f"Cache MISS for {func.__name__}")

        # Call the original function
        try:
            result = await func(*args, **kwargs)

            # Store the result in cache (offload to executor)
            await loop.run_in_executor(
                None, lambda: cache.set(key, result, expire=settings.cache_ttl)
            )

            return result
        except Exception as e:
            logger.error(f"Error executing {func.__name__}: {str(e)}")
            raise

    return wrapper


# Create the FastMCP server
mcp = FastMCP(
    SERVER_NAME,
    version=SERVER_VERSION,
    description="Documentation search and access functionality for LLMs",
    dependencies=["crawl4ai", "diskcache", "loguru", "pydantic-settings"],
)


async def fetch_documentation_content(url: str) -> Dict:
    """Fetch the content of a documentation page by direct URL."""
    logger.info(f"Fetching documentation page content from {url}")

    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)

            # Log the result for debugging
            logger.debug(f"Crawler result for URL {url}: success={result.success}")

            # Extract markdown from the result
            markdown_content = ""
            if result.markdown:
                # Check if markdown is a string or a MarkdownGenerationResult object
                if isinstance(result.markdown, str):
                    markdown_content = str(result.markdown)
                else:
                    # If it's a MarkdownGenerationResult, use the appropriate field
                    markdown_content = str(
                        getattr(result.markdown, "markdown_with_citations", "")
                        or getattr(result.markdown, "raw_markdown", "")
                    )

            # Get page title from metadata or use URL as fallback
            title = ""
            if result.metadata and isinstance(result.metadata, dict):
                title = result.metadata.get(
                    "title", url.split("/")[-1] or "Documentation"
                )
            else:
                title = url.split("/")[-1] or "Documentation"

            # Return information about the documentation page
            return {
                "url": url,
                "title": title,
                "markdown": markdown_content,
                "links": result.links or {},
                "success": result.success,
            }
    except Exception as e:
        logger.error(f"Failed to fetch documentation page content from {url}: {str(e)}")
        raise ValueError(f"Failed to fetch documentation content: {str(e)}")


# Apply caching to the fetch_documentation_content function
@async_cached
async def cached_fetch_documentation_content(url: str) -> Dict:
    """Cached version of fetch_documentation_content."""
    return await fetch_documentation_content(url)


@mcp.resource("documentation://sources")
def list_documentation_sources() -> str:
    """List all configured documentation sources."""
    logger.info("Listing all documentation sources")

    # Read the documentation URLs directly from the file to get fresh values
    documentation_urls = []

    # First check if URL is provided via environment variable
    if settings.documentation_urls_str:
        documentation_urls = [
            url.strip()
            for url in settings.documentation_urls_str.split(",")
            if url.strip()
        ]
        logger.info(
            f"Using {len(documentation_urls)} documentation URLs from environment variable"
        )
    # Otherwise read from file for real-time updates
    elif settings.documentation_urls_file_path:
        documentation_urls = settings._read_urls_from_file()
        logger.info(
            f"Hot-reloaded {len(documentation_urls)} documentation URLs from file"
        )

    results = []
    for url in documentation_urls:
        results.append(
            {"url": url, "type": "web", "description": "Web-based documentation"}
        )

    return f"Available documentation sources:\n{json.dumps(results, indent=2)}"


@mcp.tool()
def list_documentation_sources_tool() -> str:
    """List all available documentation sources this service has access to.

    This tool requires no input parameters and returns a list of documentation sources configured for this service.
    Use this tool first to discover what documentation sources are available.

    Example usage:
    ```
    list_documentation_sources_tool()
    ```

    Response provides the URLs to documentation sources and their types.
    """
    # Read the documentation URLs directly from the file to get fresh values
    documentation_urls = []

    # First check if URL is provided via environment variable
    if settings.documentation_urls_str:
        documentation_urls = [
            url.strip()
            for url in settings.documentation_urls_str.split(",")
            if url.strip()
        ]
        logger.info(
            f"Using {len(documentation_urls)} documentation URLs from environment variable"
        )
    # Otherwise read from file for real-time updates
    elif settings.documentation_urls_file_path:
        documentation_urls = settings._read_urls_from_file()
        logger.info(
            f"Hot-reloaded {len(documentation_urls)} documentation URLs from file"
        )

    results = []
    for url in documentation_urls:
        results.append(
            {"url": url, "type": "web", "description": "Web-based documentation"}
        )

    return f"Available documentation sources:\n{json.dumps(results, indent=2)}"


@mcp.tool()
async def fetch_documentation_page(url: str) -> str:
    """Fetch the content of a documentation page by URL as markdown.

    This tool retrieves the full content from a documentation page at the specified URL and returns it as markdown.
    The markdown format preserves headings, links, lists, and other formatting from the original documentation.

    Example usage:
    ```
    fetch_documentation_page(url="https://example.com/documentation/page")
    ```

    Response includes the full markdown content of the page along with metadata like title and links.
    """
    logger.info(f"Tool call: fetching documentation page content for URL: {url}")

    # Make sure the URL is properly formatted with scheme
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        result = await cached_fetch_documentation_content(url)
        logger.info("Successfully fetched documentation page content")

        if not result.get("success", True):
            return f"# Failed to load content from {url}\n\nUnable to retrieve documentation content. Please verify the URL is valid and accessible."

        title = result.get("title", "Documentation")
        markdown = result.get("markdown", "")

        return f"# {title}\n\n{markdown}"
    except Exception as e:
        logger.error(f"Error fetching documentation page: {str(e)}")
        return f"# Error retrieving documentation\n\nFailed to retrieve documentation from {url}. Error: {str(e)}"


@mcp.prompt()
def documentation_sources() -> str:
    """List all available documentation sources with their URLs and types"""
    # Get fresh documentation URLs (this will hot-reload from file if needed)
    documentation_urls = []
    if settings.documentation_urls_str:
        documentation_urls = [
            url.strip()
            for url in settings.documentation_urls_str.split(",")
            if url.strip()
        ]
    elif settings.documentation_urls_file_path:
        documentation_urls = settings._read_urls_from_file()
        logger.info(
            f"Hot-reloaded {len(documentation_urls)} documentation URLs for prompt"
        )

    # Format the response as a JSON string for consistency
    results = []
    for url in documentation_urls:
        results.append(
            {"url": url, "type": "web", "description": "Web-based documentation"}
        )

    return f"Please list all documentation sources available through this server. Here they are:\n{json.dumps(results, indent=2)}"


@mcp.prompt()
def documentation_page(url: str) -> str:
    """Fetch the full content of a documentation page at a specific URL as markdown"""
    return (
        f"Please provide the full documentation content from the following URL: {url}"
    )


@mcp.tool()
async def fetch_document_links(url: str) -> str:
    """Fetch all links from a documentation page, categorized by internal and external links.

    This tool retrieves all links from a web page at the specified URL and returns them categorized
    as internal links (within the same domain) and external links (to other domains). Use this tool
    to discover related documentation pages from a starting URL.

    Example usage:
    ```
    fetch_document_links(url="https://example.com/documentation/page")
    ```

    Response includes a structured list of internal and external links found on the page, with their
    URLs and link text when available.
    """
    logger.info(f"Tool call: fetching links from documentation page at URL: {url}")

    # Make sure the URL is properly formatted with scheme
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        result = await cached_fetch_documentation_content(url)
        logger.info("Successfully fetched links from documentation page")

        if not result.get("success", True):
            return f"# Failed to retrieve links from {url}\n\nUnable to access the page. Please verify the URL is valid and accessible."

        # Get the links from the result
        links = result.get("links", {})

        # Format the links for output
        formatted_output = [f"# Links extracted from {url}\n"]

        # Add internal links section
        internal_links = links.get("internal", [])
        formatted_output.append(f"\n## Internal Links ({len(internal_links)})\n")
        for link in internal_links:
            href = link.get("href", "")
            text = link.get("text", "").strip() or "[No text]"
            formatted_output.append(f"- [{text}]({href})")

        # Add external links section
        external_links = links.get("external", [])
        formatted_output.append(f"\n## External Links ({len(external_links)})\n")
        for link in external_links:
            href = link.get("href", "")
            text = link.get("text", "").strip() or "[No text]"
            formatted_output.append(f"- [{text}]({href})")

        return "\n".join(formatted_output)

    except Exception as e:
        logger.error(f"Error fetching links from URL {url}: {str(e)}")
        return f"# Error retrieving links\n\nFailed to retrieve links from {url}. Error: {str(e)}"


@mcp.prompt()
def documentation_links(url: str) -> str:
    """Fetch all links from a documentation page to discover related content"""
    return f"Please list all links available on the documentation page at the following URL: {url}"


def ensure_crawl4ai_setup():
    """Ensure that crawl4ai is properly set up by running the crawl4ai-setup command."""
    if settings.skip_crawl4ai_setup:
        logger.info("Skipping crawl4ai setup (docy_skip_crawl4ai_setup=true)")
        return

    logger.info("Ensuring crawl4ai is properly set up...")
    try:
        result = subprocess.run(
            ["crawl4ai-setup"], capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            logger.warning(f"crawl4ai-setup exited with code {result.returncode}")
            logger.warning(f"STDERR: {result.stderr}")
            logger.warning(
                "crawl4ai setup might be incomplete, but we'll try to continue anyway"
            )
        else:
            logger.info("crawl4ai setup completed successfully")

    except FileNotFoundError:
        logger.error(
            "crawl4ai-setup command not found. Some functionality may be limited."
        )
    except Exception as e:
        logger.error(f"Error running crawl4ai-setup: {str(e)}")
        logger.warning(
            "Continuing despite setup failure, but functionality may be limited"
        )


async def cache_documentation_urls():
    """Pre-cache all documentation URLs configured in settings."""
    docs_urls = settings.documentation_urls
    if not docs_urls:
        logger.warning("No documentation URLs to cache")
        return

    logger.info(f"Pre-caching {len(docs_urls)} documentation URLs...")

    # Get cache statistics before pre-caching
    cache_size_before = cache.volume()

    for url in docs_urls:
        try:
            logger.info(f"Pre-caching documentation URL: {url}")
            await cached_fetch_documentation_content(url)
            logger.info(f"Successfully cached content from {url}")
        except Exception as e:
            logger.error(f"Failed to cache documentation URL {url}: {str(e)}")

    # Get cache statistics after pre-caching
    cache_size_after = cache.volume()
    logger.info(
        f"Cache size: {cache_size_before / 1024:.2f} KB -> {cache_size_after / 1024:.2f} KB"
    )


def create_server() -> FastMCP:
    """Create and configure the MCP server instance."""
    global cache

    # Initialize the diskcache Cache
    cache_dir = settings.cache_directory
    logger.info(f"Initializing disk cache at: {cache_dir}")

    # Ensure parent directory exists if cache_dir has a parent path
    parent_dir = os.path.dirname(cache_dir)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    # Initialize the cache with disk-based persistence
    cache = Cache(cache_dir)

    # Configure cache settings
    cache.reset("size_limit", int(1e9))  # Default to 1GB size limit
    logger.info(f"Disk cache initialized with TTL: {settings.cache_ttl}s")

    # Ensure crawl4ai is properly set up
    ensure_crawl4ai_setup()

    # Pre-cache documentation URLs
    if settings.documentation_urls:
        logger.info("Pre-caching documentation URLs...")
        asyncio.run(cache_documentation_urls())

    # Log server creation
    logger.info(f"Created MCP server with name: {SERVER_NAME}")
    logger.info(
        f"Configured with {len(settings.documentation_urls)} documentation URLs and cache TTL: {settings.cache_ttl}s"
    )

    # Note: URL caching will be initiated in __main__.py after server startup

    return mcp
