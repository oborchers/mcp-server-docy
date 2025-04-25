# Docy SSE Server

This directory contains configuration for running Docy as a persistent SSE (Server-Sent Events) server that can be shared across multiple projects. This setup allows you to:

1. Use a single shared Docy instance across all your projects
2. Maintain a collective documentation URLs file
3. Share the documentation cache to improve performance
4. Configure Claude Code in each project to connect to this central server

## Quick Start

```bash
# From the root of the mcp-server-docy repository
cd sse-server
cp .docy.example.urls .docy.urls  # Create your URLs file from the example
make run
```

## Configuration

The server uses the following configuration:

- **Port:** 6274 (configurable in the Makefile)
- **Shared URLs file:** Located at `sse-server/.docy.urls`
- **Shared cache:** Located at `sse-server/.docy.cache`
- **Container name:** `docy-sse-server`

## Usage

### Starting the Server

```bash
# From the sse-server directory
make run
```

This will:
1. Pull the latest Docy image
2. Start a container with SSE transport enabled
3. Mount the shared URLs file and cache directory
4. Make the server available at http://localhost:6274

### Stopping the Server

```bash
# From the sse-server directory
make stop
```

### Restarting the Server

```bash
# From the sse-server directory
make restart
```

### Reloading the URLs File

If you've updated the `.docy.urls` file and want the changes to take effect:

```bash
# From the sse-server directory
make reload-urls
```

## Configuring Projects to Use the Shared Server

In each project where you want to use the shared Docy server, create a `.mcp.json` file with:

```json
{
  "mcp": {
    "servers": {
      "docy": {
        "type": "sse",
        "url": "http://localhost:6274/sse"
      }
    }
  }
}
```

## Managing Documentation Sources

Edit the shared `.docy.urls` file to add or remove documentation sources:

```
# Official documentation
https://docs.crawl4ai.com/
https://grantjenks.com/docs/diskcache/tutorial.html

# Project documentation
https://fastmcp.readthedocs.io/
https://react.dev/
```

## Benefits of This Approach

- **Efficiency:** Single server instance for all projects reduces resource usage
- **Consistency:** Same documentation available across all projects
- **Performance:** Shared cache means faster responses for all projects
- **Management:** Central place to add/remove documentation sources
- **Scalability:** Easy to add new projects without additional server instances

## Troubleshooting

If you have issues connecting:

1. Verify the server is running: `docker ps | grep docy-sse-server`
2. Check the container logs: `docker logs docy-sse-server`
3. Ensure your `.mcp.json` uses the correct port
4. Verify the URLs file contains valid documentation URLs