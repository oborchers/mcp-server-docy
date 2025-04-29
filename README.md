![Docy Logo](media/logo.png)

# Docy: Documentation at Your AI's Fingertips

**Supercharge your AI assistant with instant access to technical documentation.**

Docy gives your AI direct access to the technical documentation it needs, right when it needs it. No more outdated information, broken links, or rate limits - just accurate, real-time documentation access for more precise coding assistance.

## Why Choose Docy?

- **Instant Documentation Access**: Direct access to docs from React, Python, crawl4ai, and any other tech stack you use
- **Hot-Reload Support**: Add new documentation sources on-the-fly without restarting - just edit the .docy.urls file!
- **Intelligent Caching**: Reduces latency and external requests while maintaining fresh content
- **Self-Hosted Control**: Keep your documentation access within your security perimeter
- **Seamless MCP Integration**: Works effortlessly with Claude, VS Code, and other MCP-enabled AI tools

> **Note**: Claude may default to using its built-in WebFetchTool instead of Docy. To explicitly request Docy's functionality, use a callout like: "Please use Docy to find..."

# Docy MCP Server

A Model Context Protocol server that provides documentation access capabilities. This server enables LLMs to search and retrieve content from documentation websites by scraping them with crawl4ai. Built with FastMCP v2.

## Using Docy

Here are examples of how Docy can help with common documentation tasks:

```
# Verify implementation against documentation
Are we implementing Crawl4Ai scrape results correctly? Let's check the documentation.

# Explore API usage patterns
What do the docs say about using mcp.tool? Show me examples from the documentation.

# Compare implementation options
How should we structure our data according to the React documentation? What are the best practices?
```

With Docy, Claude Code can directly access and analyze documentation from configured sources, making it more effective at providing accurate, documentation-based guidance.

To ensure Claude Code prioritizes Docy for documentation-related tasks, add the following guidelines to your project's `CLAUDE.md` file:

```
## Documentation Guidelines
- When checking documentation, prefer using Docy over WebFetchTool
- Use list_documentation_sources_tool to discover available documentation sources
- Use fetch_documentation_page to retrieve full documentation pages
- Use fetch_document_links to discover related documentation
```

Adding these instructions to your `CLAUDE.md` file helps Claude Code consistently use Docy instead of its built-in web fetch capabilities when working with documentation.


### Available Tools

- `list_documentation_sources_tool` - List all available documentation sources
  - No parameters required

- `fetch_documentation_page` - Fetch the content of a documentation page by URL as markdown
  - `url` (string, required): The URL to fetch content from

- `fetch_document_links` - Fetch all links from a documentation page
  - `url` (string, required): The URL to fetch links from

### Prompts

- **documentation_sources**
  - List all available documentation sources with their URLs and types
  - No arguments required

- **documentation_page**
  - Fetch the full content of a documentation page at a specific URL as markdown
  - Arguments:
    - `url` (string, required): URL of the specific documentation page to get

- **documentation_links**
  - Fetch all links from a documentation page to discover related content
  - Arguments:
    - `url` (string, required): URL of the documentation page to get links from

## Installation

### Using uv (recommended)

When using [`uv`](https://docs.astral.sh/uv/) no specific installation is needed. We will
use [`uvx`](https://docs.astral.sh/uv/guides/tools/) to directly run *mcp-server-docy*.

### Using PIP

Alternatively you can install `mcp-server-docy` via pip:

```
pip install mcp-server-docy
```

After installation, you can run it as a script using:

```
DOCY_DOCUMENTATION_URLS="https://docs.crawl4ai.com/,https://react.dev/" python -m mcp_server_docy
```

### Using Docker

You can also use the Docker image:

```
docker pull oborchers/mcp-server-docy:latest
docker run -i --rm -e DOCY_DOCUMENTATION_URLS="https://docs.crawl4ai.com/,https://react.dev/" oborchers/mcp-server-docy
```

### Global Server Setup

For teams or multi-project development, check out the `server/README.md` for instructions on running a persistent SSE server that can be shared across multiple projects. This setup allows you to maintain a single Docy instance with shared documentation URLs and cache.

## Configuration

### Configure for Claude.app

Add to your Claude settings:

<details>
<summary>Using uvx</summary>

```json
"mcpServers": {
  "docy": {
    "command": "uvx",
    "args": ["mcp-server-docy"],
    "env": {
      "DOCY_DOCUMENTATION_URLS": "https://docs.crawl4ai.com/,https://react.dev/"
    }
  }
}
```
</details>

<details>
<summary>Using docker</summary>

```json
"mcpServers": {
  "docy": {
    "command": "docker",
    "args": ["run", "-i", "--rm", "oborchers/mcp-server-docy:latest"],
    "env": {
      "DOCY_DOCUMENTATION_URLS": "https://docs.crawl4ai.com/,https://react.dev/"
    }
  }
}
```
</details>

<details>
<summary>Using pip installation</summary>

```json
"mcpServers": {
  "docy": {
    "command": "python",
    "args": ["-m", "mcp_server_docy"],
    "env": {
      "DOCY_DOCUMENTATION_URLS": "https://docs.crawl4ai.com/,https://react.dev/"
    }
  }
}
```
</details>

### Configure for VS Code

For manual installation, add the following JSON block to your User Settings (JSON) file in VS Code. You can do this by pressing `Ctrl + Shift + P` and typing `Preferences: Open User Settings (JSON)`.

Optionally, you can add it to a file called `.vscode/mcp.json` in your workspace. This will allow you to share the configuration with others.

> Note that the `mcp` key is needed when using the `mcp.json` file.

<details>
<summary>Using uvx</summary>

```json
{
  "mcp": {
    "servers": {
      "docy": {
        "command": "uvx",
        "args": ["mcp-server-docy"],
        "env": {
          "DOCY_DOCUMENTATION_URLS": "https://docs.crawl4ai.com/,https://react.dev/"
        }
      }
    }
  }
}
```
</details>

<details>
<summary>Using Docker</summary>

```json
{
  "mcp": {
    "servers": {
      "docy": {
        "command": "docker",
        "args": ["run", "-i", "--rm", "oborchers/mcp-server-docy:latest"],
        "env": {
          "DOCY_DOCUMENTATION_URLS": "https://docs.crawl4ai.com/,https://react.dev/"
        }
      }
    }
  }
}
```
</details>

### Configuration Options

The application can be configured using environment variables:

- `DOCY_DOCUMENTATION_URLS` (string): Comma-separated list of URLs to documentation sites to include (e.g., "https://docs.crawl4ai.com/,https://react.dev/")
- `DOCY_DOCUMENTATION_URLS_FILE` (string): Path to a file containing documentation URLs, one per line (default: ".docy.urls")
- `DOCY_CACHE_TTL` (integer): Cache time-to-live in seconds (default: 432000)
- `DOCY_CACHE_DIRECTORY` (string): Path to the cache directory (default: ".docy.cache")
- `DOCY_USER_AGENT` (string): Custom User-Agent string for HTTP requests
- `DOCY_DEBUG` (boolean): Enable debug logging ("true", "1", "yes", or "y")
- `DOCY_SKIP_CRAWL4AI_SETUP` (boolean): Skip running the crawl4ai-setup command at startup ("true", "1", "yes", or "y")
- `DOCY_TRANSPORT` (string): Transport protocol to use (options: "sse" or "stdio", default: "stdio")
- `DOCY_HOST` (string): Host address to bind the server to (default: "127.0.0.1")
- `DOCY_PORT` (integer): Port to run the server on (default: 8000)

Environment variables can be set directly or via a `.env` file.

### URL Configuration File

As an alternative to setting the `DOCY_DOCUMENTATION_URLS` environment variable, you can create a `.docy.urls` file in your project directory with one URL per line:

```
https://docs.crawl4ai.com/
https://react.dev/
# Lines starting with # are treated as comments
https://docs.python.org/3/
```

This approach is especially useful for:
- Projects where you want to share documentation sources with your team
- Repositories where storing URLs in version control is beneficial
- Situations where you want to avoid long environment variable values

The server will first check for URLs in the `DOCY_DOCUMENTATION_URLS` environment variable, and if none are found, it will look for the `.docy.urls` file.

#### Hot Reload for URL File

When using the `.docy.urls` file for documentation sources, the server implements a hot-reload mechanism that reads the file on each request rather than caching the URLs. This means you can:

1. Add, remove, or modify documentation URLs in the `.docy.urls` file while the server is running
2. See those changes reflected immediately in subsequent calls to `list_documentation_sources_tool` or other documentation tools
3. Avoid restarting the server when modifying your documentation sources

This is particularly useful during development or when you need to quickly add new documentation sources to a running server.

### Documentation URL Best Practices

The URLs you configure should ideally point to documentation index or introduction pages that contain:

- Tables of contents
- Navigation structures
- Collections of internal and external links

This allows the LLM to:
1. Start at a high-level documentation page
2. Discover relevant subpages via links
3. Navigate to specific documentation as needed

Using documentation sites with well-structured subpages is highly recommended as it:
- Minimizes context usage by allowing the LLM to focus on relevant sections
- Improves navigation efficiency through documentation
- Provides a natural way to explore and find information
- Reduces the need to load entire documentation sets at once

For example, instead of loading an entire documentation site, the LLM can start at the index page, identify the relevant section, and then navigate to specific subpages as needed.

### Caching Behavior

The MCP server automatically caches documentation content to improve performance:

- At startup, the server pre-fetches and caches all configured documentation URLs from `DOCY_DOCUMENTATION_URLS`
- The cache time-to-live (TTL) can be configured via the `DOCY_CACHE_TTL` environment variable
- Each new site accessed is automatically loaded into cache to reduce traffic and improve response times
- Cached content is stored in a persistent disk-based cache using the `diskcache` library
- The cache location can be configured via the `DOCY_CACHE_DIRECTORY` environment variable (default: ".docy.cache")
- The cache persists between server restarts, providing better performance for frequently accessed documentation

#### Exceptions to Caching

While most content is cached for performance, there are specific exceptions:

- **Documentation URL Lists**: When using the `.docy.urls` file, the list of documentation sources is never cached - instead, the file is re-read on each request to support hot-reloading of URLs
- **Page Content**: The actual content of documentation pages is still cached according to the configured TTL

This hybrid approach offers both performance benefits for content access and flexibility for documentation source management.

## Local Development
- Run in development mode: `fastmcp dev src/mcp_server_docy/__main__.py --with-editable .`
- Access API at: `http://127.0.0.1:6274`
- Run with MCP inspector: `uv run --with fastmcp --with-editable /Users/oliverborchers/Desktop/Code.nosync/mcp-server-docy --with crawl4ai --with loguru --with diskcache --with pydantic-settings fastmcp run src/mcp_server_docy/__main__.py`

## Debugging

You can use the MCP inspector to debug the server. For uvx installations:

```
DOCY_DOCUMENTATION_URLS="https://docs.crawl4ai.com/" npx @modelcontextprotocol/inspector uvx mcp-server-docy
```

Or if you've installed the package in a specific directory or are developing on it:

```
cd path/to/docy
DOCY_DOCUMENTATION_URLS="https://docs.crawl4ai.com/" npx @modelcontextprotocol/inspector uv run mcp-server-docy
```

### Troubleshooting: "Tool not found" Error in Claude Code CLI

If you encounter errors like "ERROR Tool not found for mcp__docy__fetch_documentation_page" in Claude Code CLI, follow these steps:

1. Create a `.docy.urls` file in your current directory with your documentation URLs:
```
https://docs.crawl4ai.com/
https://react.dev/
```

2. Run the server using Docker with the SSE transport protocol and mount the URLs file:

```bash
docker run -i --rm -p 8000:8000 \
  -e DOCY_TRANSPORT=sse \
  -e DOCY_HOST=0.0.0.0 \
  -e DOCY_PORT=8000 \
  -v "$(pwd)/.docy.urls:/app/.docy.urls" \
  oborchers/mcp-server-docy
```

3. Configure your Claude Code `.mcp.json` to use the SSE endpoint:

```json
{
  "mcp": {
    "servers": {
      "docy": {
        "type": "sse",
        "url": "http://localhost:8000/sse"
      }
    }
  }
}
```

This configuration:
- Uses a mounted `.docy.urls` file instead of environment variables for documentation sources
- Switches from the default stdio mode to SSE (Server-Sent Events) protocol
- Makes the server accessible from outside the container
- Exposes the server on port 8000 for HTTP access

The SSE transport is recommended when running the server as a standalone service that needs to be accessed over HTTP, which is particularly useful for Docker deployments.

## Release Process

The project uses GitHub Actions for automated releases:

1. Update the version in `pyproject.toml`
2. Create a new tag with `git tag vX.Y.Z` (e.g., `git tag v0.1.0`)
3. Push the tag with `git push --tags`

This will automatically:
- Verify the version in `pyproject.toml` matches the tag
- Run tests and lint checks
- Build and publish to PyPI
- Build and publish to Docker Hub as `oborchers/mcp-server-docy:latest` and `oborchers/mcp-server-docy:X.Y.Z`

## Contributing

We encourage contributions to help expand and improve mcp-server-docy. Whether you want to add new features, enhance existing functionality, or improve documentation, your input is valuable.

For examples of other MCP servers and implementation patterns, see:
https://github.com/modelcontextprotocol/servers

Pull requests are welcome! Feel free to contribute new ideas, bug fixes, or enhancements to make mcp-server-docy even more powerful and useful.

## License

mcp-server-docy is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.