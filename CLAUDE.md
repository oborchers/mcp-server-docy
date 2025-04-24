# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Documentation Guidelines
- When checking documentation, prefer using Docy over WebFetchTool
- Use list_documentation_sources_tool to discover available documentation sources
- Use fetch_documentation_page to retrieve full documentation pages
- Use fetch_document_links to discover related documentation

## Commands
- Run server: `uv run mcp-server-docy`
- Run tests: `uv run pytest -xvs tests/`
- Run single test: `uv run pytest -xvs tests/test_server.py::test_function_name`
- Lint code: `uv run ruff check --fix ./src/`
- Format code: `uv run ruff format ./src/`
- Type check: `uv run pyright ./src/`
- Build package: `uv run build`
- Publish package: `uv run twine upload dist/*`

## Local Development
- Run in development mode: `fastmcp dev src/mcp_server_docy/__main__.py --with-editable .`
- Access API at: `http://127.0.0.1:6274`
- Run with MCP inspector: `uv run --with fastmcp --with-editable /Users/oliverborchers/Desktop/Code.nosync/mcp-server-docy --with crawl4ai --with loguru --with diskcache --with pydantic-settings fastmcp run src/mcp_server_docy/__main__.py`

## Code Style
- Use double quotes for strings
- Sort imports: 1) standard library, 2) third-party, 3) local
- Type hints required for all function parameters and return values
- Use snake_case for variables and functions, PascalCase for classes
- Include detailed docstrings for all modules, classes, and functions
- Handle exceptions with proper error logging using loguru
- Structure code as: 1) imports, 2) constants, 3) classes, 4) functions, 5) main code
- Use async/await patterns consistently for asynchronous operations
- Use descriptive variable names that indicate purpose and type
- For cached operations, use the @async_cached decorator
- Always validate environment variables and provide clear error messages