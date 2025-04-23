from typing import Dict, List, Optional
import json
import asyncio
import subprocess
from cachetools import TTLCache
from functools import wraps
from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from fastmcp import FastMCP
from crawl4ai import AsyncWebCrawler

# Remove default handler to allow configuration from __main__.py
logger.remove()

# Server metadata
SERVER_NAME = "Docy"
SERVER_VERSION = "0.1.0"
DEFAULT_USER_AGENT = f"ModelContextProtocol/1.0 {SERVER_NAME} (+https://github.com/modelcontextprotocol/servers)"


class Settings(BaseSettings):
    """Configuration settings for the Docy server."""
    model_config = SettingsConfigDict(extra="ignore", env_file=".env")

    docy_user_agent: str = Field(default=DEFAULT_USER_AGENT, description="Custom User-Agent string for HTTP requests")
    docy_documentation_urls: Optional[str] = Field(
        default=None, 
        description="Comma-separated list of URLs to documentation sites to include"
    )
    docy_cache_ttl: int = Field(default=3600, description="Cache time-to-live in seconds")
    docy_debug: bool = Field(default=False, description="Enable debug logging")
    docy_skip_crawl4ai_setup: bool = Field(default=False, description="Skip running crawl4ai-setup command at startup")
    
    @property
    def user_agent(self) -> str:
        return self.docy_user_agent
    
    @property
    def cache_ttl(self) -> int:
        return self.docy_cache_ttl
    
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
    def documentation_urls(self) -> List[str]:
        """Parse the comma-separated URLs into a list."""
        # Add debug output to help diagnose environment variable issues
        logger.debug(f"Documentation URLs string: '{self.documentation_urls_str}'")
        
        if not self.documentation_urls_str:
            logger.warning("No documentation URLs provided via environment variables")
            return []
            
        # Split by comma and strip whitespace from each URL
        urls = [url.strip() for url in self.documentation_urls_str.split(',') if url.strip()]
        logger.debug(f"Parsed {len(urls)} documentation URLs: {urls}")
        return urls


settings = Settings()

# HTTP request cache (will be initialized in create_server)
_http_cache = None
_cache_lock = asyncio.Lock()


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


# Create the FastMCP server
mcp = FastMCP(
    SERVER_NAME, 
    version=SERVER_VERSION,
    description="Documentation search and access functionality for LLMs",
    dependencies=["crawl4ai", "cachetools", "loguru", "pydantic-settings"],
)


@async_cached(_http_cache)
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
                    markdown_content = result.markdown
                else:
                    # If it's a MarkdownGenerationResult, use the appropriate field
                    markdown_content = getattr(result.markdown, "markdown_with_citations", "") or \
                                     getattr(result.markdown, "raw_markdown", "")
            
            # Get page title from metadata or use URL as fallback
            title = ""
            if result.metadata and isinstance(result.metadata, dict):
                title = result.metadata.get("title", url.split("/")[-1] or "Documentation")
            else:
                title = url.split("/")[-1] or "Documentation"
            
            # Return information about the documentation page
            return {
                "url": url,
                "title": title,
                "markdown": markdown_content,
                "links": result.links or {},
                "success": result.success
            }
    except Exception as e:
        logger.error(f"Failed to fetch documentation page content from {url}: {str(e)}")
        raise ValueError(f"Failed to fetch documentation content: {str(e)}")


@mcp.resource("documentation://{url}")
async def get_documentation(url: str) -> str:
    """Get documentation content for a specific URL."""
    logger.info(f"Resource request for documentation URL: {url}")
    result = await fetch_documentation_content(url)
    
    if not result.get('success', True):
        return f"# Failed to load content from {url}\n\nUnable to retrieve documentation content. Please verify the URL is valid and accessible."
    
    title = result.get('title', 'Documentation')
    markdown = result.get('markdown', '')
    
    return f"# {title}\n\n{markdown}"


@mcp.resource("documentation://sources")
def list_documentation_sources() -> str:
    """List all configured documentation sources."""
    logger.info("Listing all documentation sources")
    
    # Access the configuration via settings
    documentation_urls = settings.documentation_urls
    
    results = []
    for url in documentation_urls:
        results.append({
            "url": url,
            "type": "web",
            "description": "Web-based documentation"
        })
    
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
    # Access the configuration via settings
    documentation_urls = settings.documentation_urls
    logger.info(f"Tool call: listing {len(documentation_urls)} documentation sources")
    
    results = []
    for url in documentation_urls:
        results.append({
            "url": url,
            "type": "web",
            "description": "Web-based documentation"
        })
    
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
    
    try:
        result = await fetch_documentation_content(url)
        logger.info(f"Successfully fetched documentation page content")
        
        if not result.get('success', True):
            return f"# Failed to load content from {url}\n\nUnable to retrieve documentation content. Please verify the URL is valid and accessible."
        
        title = result.get('title', 'Documentation')
        markdown = result.get('markdown', '')
        
        return f"# {title}\n\n{markdown}"
    except Exception as e:
        logger.error(f"Error fetching documentation page: {str(e)}")
        raise


@mcp.prompt()
def documentation_sources() -> str:
    """List all available documentation sources with their URLs and types"""
    return "Please list all documentation sources available through this server."


@mcp.prompt()
def documentation_page(url: str) -> str:
    """Fetch the full content of a documentation page at a specific URL as markdown"""
    return f"Please provide the full documentation content from the following URL: {url}"


def ensure_crawl4ai_setup():
    """Ensure that crawl4ai is properly set up by running the crawl4ai-setup command."""
    if settings.skip_crawl4ai_setup:
        logger.info("Skipping crawl4ai setup (docy_skip_crawl4ai_setup=true)")
        return
        
    logger.info("Ensuring crawl4ai is properly set up...")
    try:
        result = subprocess.run(
            ["crawl4ai-setup"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            logger.warning(f"crawl4ai-setup exited with code {result.returncode}")
            logger.warning(f"STDERR: {result.stderr}")
            logger.warning("crawl4ai setup might be incomplete, but we'll try to continue anyway")
        else:
            logger.info("crawl4ai setup completed successfully")
            
    except FileNotFoundError:
        logger.error("crawl4ai-setup command not found. Some functionality may be limited.")
    except Exception as e:
        logger.error(f"Error running crawl4ai-setup: {str(e)}")
        logger.warning("Continuing despite setup failure, but functionality may be limited")


def create_server() -> FastMCP:
    """Create and configure the MCP server instance."""
    global _http_cache
    
    # Initialize the HTTP cache
    _http_cache = TTLCache(maxsize=500, ttl=settings.cache_ttl)
    
    # Ensure crawl4ai is properly set up
    ensure_crawl4ai_setup()
    
    logger.info(f"Created MCP server with name: {SERVER_NAME}")
    logger.info(f"Configured with {len(settings.documentation_urls)} documentation URLs and cache TTL: {settings.cache_ttl}s")
    
    return mcp