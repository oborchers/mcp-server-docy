# Docy MCP Server

A Model Context Protocol server that provides documentation access capabilities. This server enables LLMs to search and retrieve content from documentation websites by scraping them with crawl4ai. Built with FastMCP v2.

### Available Tools

- `list_documentation` - List all available documentation sites
  - No parameters required

- `get_doc_toc` - Get the table of contents for a specific documentation site
  - `doc_index` (integer, required): Index of the documentation site to access

- `get_doc_page` - Get a specific page from a documentation site
  - `doc_index` (integer, required): Index of the documentation site to access
  - `url` (string, required): URL of the specific documentation page to get

### Prompts

- **list_docs**
  - List all available documentation sites
  - No arguments required

- **doc_toc**
  - Get the table of contents for a specific documentation site
  - Arguments:
    - `doc_index` (integer, required): Index of the documentation site to access

- **doc_page**
  - Get a specific page from a documentation site
  - Arguments:
    - `doc_index` (integer, required): Index of the documentation site to access
    - `url` (string, required): URL of the specific documentation page to get

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
DOCY_DOCUMENTATION_URLS="https://docs.python.org/3/,https://react.dev/" python -m mcp_server_docy
```

### Using Docker

You can also use the Docker image:

```
docker pull oborchers/mcp-server-docy:latest
docker run -i --rm -e DOCY_DOCUMENTATION_URLS="https://docs.python.org/3/,https://react.dev/" oborchers/mcp-server-docy
```

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
      "DOCY_DOCUMENTATION_URLS": "https://docs.python.org/3/,https://react.dev/"
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
      "DOCY_DOCUMENTATION_URLS": "https://docs.python.org/3/,https://react.dev/"
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
      "DOCY_DOCUMENTATION_URLS": "https://docs.python.org/3/,https://react.dev/"
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
          "DOCY_DOCUMENTATION_URLS": "https://docs.python.org/3/,https://react.dev/"
        }
      }
    }
  }
}
```
</details>

### Configuration Options

The application can be configured using environment variables:

- `DOCY_DOCUMENTATION_URLS` (string): Comma-separated list of URLs to documentation sites to include (e.g., "https://docs.python.org/3/,https://react.dev/")
- `DOCY_CACHE_TTL` (integer): Cache time-to-live in seconds (default: 3600)
- `DOCY_USER_AGENT` (string): Custom User-Agent string for HTTP requests
- `DOCY_DEBUG` (boolean): Enable debug logging ("true", "1", "yes", or "y")
- `DOCY_SKIP_CRAWL4AI_SETUP` (boolean): Skip running the crawl4ai-setup command at startup ("true", "1", "yes", or "y")

Environment variables can be set directly or via a `.env` file.

## Debugging

You can use the MCP inspector to debug the server. For uvx installations:

```
DOCY_DOCUMENTATION_URLS="https://docs.python.org/3/" npx @modelcontextprotocol/inspector uvx mcp-server-docy
```

Or if you've installed the package in a specific directory or are developing on it:

```
cd path/to/docy
DOCY_DOCUMENTATION_URLS="https://docs.python.org/3/" npx @modelcontextprotocol/inspector uv run mcp-server-docy
```

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