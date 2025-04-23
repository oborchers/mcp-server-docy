# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run server: `uv run mcp-server-docy`
- Run tests: `uv run pytest -xvs tests/`
- Run single test: `uv run pytest -xvs tests/test_server.py::test_function_name`
- Lint code: `uv run ruff check --fix ./src/`
- Format code: `uv run ruff format ./src/`
- Type check: `uv run pyright ./src/`
- Build package: `uv run build`

## Code Style
- Use double quotes for strings
- Sort imports with standard library first, then third-party, then local
- Type hints required for function parameters and return values
- Use snake_case for variables and functions, PascalCase for classes
- Include docstrings for all modules, classes, and functions
- Handle exceptions with proper error logging using loguru
- Structure: 1) imports, 2) constants, 3) classes, 4) functions, 5) main code