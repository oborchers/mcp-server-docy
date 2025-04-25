#!/usr/bin/env python3
from mcp_server_docy import setup
from mcp_server_docy.server import settings

mcp = setup()


def main():
    # Use settings from environment variables
    if settings.transport == "sse":
        # For SSE transport, include host and port settings
        mcp.run(
            transport=settings.transport,
            host=settings.host,
            port=settings.port,
        )
    else:
        # For stdio transport, host and port don't apply
        mcp.run(transport=settings.transport)


if __name__ == "__main__":
    main()
