import sys
from loguru import logger
from .server import create_server, settings, mcp

__version__ = "0.1.0"


def main():
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
    logger.debug(f"Environment configuration:")
    logger.debug(f"  DOCY_DEBUG: {settings.debug}")
    logger.debug(f"  DOCY_CACHE_TTL: {settings.cache_ttl}")
    logger.debug(f"  DOCY_USER_AGENT: {settings.user_agent}")
    logger.debug(f"  DOCY_DOCUMENTATION_URLS: {settings.documentation_urls_str}")

    logger.info(f"Starting mcp-docy server with logging level: {log_level}")
    
    if settings.documentation_urls:
        logger.info(f"Documentation URLs: {', '.join(settings.documentation_urls)}")
    else:
        logger.warning("No documentation URLs provided. The server will have no content to serve.")

    # Create and configure the server
    server = create_server()

    try:
        # Run the server with the FastMCP's built-in runner
        server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by keyboard interrupt")
    except Exception as e:
        logger.exception(f"Server failed with error: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("Server shutdown complete")


if __name__ == "__main__":
    main()