import sys
from loguru import logger
from .server import create_server, settings

__all__ = ["settings"]


def setup():
    """MCP Docy Server - Documentation search and access functionality for MCP"""
    # Configure logging level based on settings
    log_level = "DEBUG" if settings.debug else "INFO"
    logger.configure(
        handlers=[
            {
                "sink": sys.stderr,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                "level": log_level,
            }
        ]
    )

    # Log environment variables for debugging
    logger.debug("Environment configuration:")
    logger.debug(f"  docy_debug: {settings.debug}")
    logger.debug(f"  docy_cache_ttl: {settings.cache_ttl}")
    logger.debug(f"  docy_cache_directory: {settings.cache_directory}")
    logger.debug(f"  docy_user_agent: {settings.user_agent}")
    logger.debug(f"  docy_documentation_urls: {settings.documentation_urls_str}")
    logger.debug(
        f"  docy_documentation_urls_file: {settings.documentation_urls_file_path}"
    )

    logger.info(f"Starting mcp-docy server with logging level: {log_level}")

    if settings.documentation_urls:
        logger.info(f"Documentation URLs: {', '.join(settings.documentation_urls)}")
        # Log the source of the URLs
        if settings.documentation_urls_str:
            logger.debug("URLs source: environment variable DOCY_DOCUMENTATION_URLS")
        else:
            logger.debug(f"URLs source: file {settings.documentation_urls_file_path}")
    else:
        logger.warning(
            "No documentation URLs provided. The server will have no content to serve."
        )

    # Create and configure the server
    server = create_server()
    return server
