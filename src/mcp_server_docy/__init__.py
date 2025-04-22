import sys
import asyncio
import argparse
from loguru import logger
from .server import serve


def main():
    """MCP Docy Server - Documentation search and access functionality for MCP"""
    parser = argparse.ArgumentParser(
        description="give a model the ability to access and query documentation"
    )
    parser.add_argument("--user-agent", type=str, help="Custom User-Agent string")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--documentation", 
        type=str, 
        nargs="+", 
        help="URLs to documentation sites to include (can specify multiple)"
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=3600,
        help="Cache time-to-live in seconds (default: 3600)"
    )

    args = parser.parse_args()

    # Configure logging level based on arguments
    log_level = "DEBUG" if args.debug else "INFO"
    logger.configure(
        handlers=[
            {
                "sink": sys.stderr,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                "level": log_level,
            }
        ]
    )

    logger.info(f"Starting mcp-docy server with logging level: {log_level}")

    try:
        asyncio.run(serve(args.user_agent, args.documentation, args.cache_ttl))
    except KeyboardInterrupt:
        logger.info("Server interrupted by keyboard interrupt")
    except Exception as e:
        logger.exception(f"Server failed with error: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("Server shutdown complete")


if __name__ == "__main__":
    main()