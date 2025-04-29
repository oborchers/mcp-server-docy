import os
import tempfile
import json
from unittest.mock import patch
from mcp_server_docy.server import (
    Settings,
    SERVER_NAME,
    list_documentation_sources_tool,
    list_documentation_sources,
    documentation_sources,
)


def test_settings():
    """Test that the Settings class can be instantiated."""
    settings = Settings()
    assert settings.user_agent.startswith("ModelContextProtocol")


def test_server_metadata():
    """Test server metadata constants."""
    assert SERVER_NAME == "Docy"


def test_read_urls_from_env():
    """Test that URLs are correctly read from environment variable."""
    os.environ["DOCY_DOCUMENTATION_URLS"] = (
        "https://docs.example.com/,https://api.example.org/"
    )
    settings = Settings()

    # URLs from environment should take precedence
    urls = settings.documentation_urls
    assert len(urls) == 2
    assert "https://docs.example.com/" in urls
    assert "https://api.example.org/" in urls


def test_read_urls_from_file():
    """Test that URLs are correctly read from file."""
    # First unset any environment variable to ensure file takes precedence
    if "DOCY_DOCUMENTATION_URLS" in os.environ:
        del os.environ["DOCY_DOCUMENTATION_URLS"]

    # Create a temporary file with URLs
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        tmp.write("# Test URLs\n")
        tmp.write("https://test1.example.com/\n")
        tmp.write("https://test2.example.com/\n")
        tmp.write("# Comment line\n")
        tmp.write("https://test3.example.com/\n")
        tmp_path = tmp.name

    try:
        os.environ["DOCY_DOCUMENTATION_URLS_FILE"] = tmp_path
        settings = Settings()

        urls = settings.documentation_urls
        assert len(urls) == 3
        assert "https://test1.example.com/" in urls
        assert "https://test2.example.com/" in urls
        assert "https://test3.example.com/" in urls
        assert "# Comment line" not in urls
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if "DOCY_DOCUMENTATION_URLS_FILE" in os.environ:
            del os.environ["DOCY_DOCUMENTATION_URLS_FILE"]
        if "DOCY_DOCUMENTATION_URLS" in os.environ:
            del os.environ["DOCY_DOCUMENTATION_URLS"]


def test_hot_reload_urls_from_file():
    """Test that URLs are correctly hot-reloaded from file each time."""
    # First unset any environment variable to ensure file takes precedence
    if "DOCY_DOCUMENTATION_URLS" in os.environ:
        del os.environ["DOCY_DOCUMENTATION_URLS"]

    # Create a temporary file with initial URLs
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        tmp.write("https://initial1.example.com/\n")
        tmp.write("https://initial2.example.com/\n")
        tmp_path = tmp.name

    try:
        os.environ["DOCY_DOCUMENTATION_URLS_FILE"] = tmp_path
        settings = Settings()

        # First call - should get initial URLs
        with patch("mcp_server_docy.server.settings", settings):
            result1 = list_documentation_sources_tool()
            parsed1 = json.loads(result1.split("\n", 1)[1])
            assert len(parsed1) == 2
            urls1 = [item["url"] for item in parsed1]
            assert "https://initial1.example.com/" in urls1
            assert "https://initial2.example.com/" in urls1

        # Now update the file with new URLs
        with open(tmp_path, "w") as f:
            f.write("https://updated1.example.com/\n")
            f.write("https://updated2.example.com/\n")
            f.write("https://updated3.example.com/\n")

        # Second call - should get updated URLs (hot reload)
        with patch("mcp_server_docy.server.settings", settings):
            result2 = list_documentation_sources_tool()
            parsed2 = json.loads(result2.split("\n", 1)[1])
            assert len(parsed2) == 3
            urls2 = [item["url"] for item in parsed2]
            assert "https://updated1.example.com/" in urls2
            assert "https://updated2.example.com/" in urls2
            assert "https://updated3.example.com/" in urls2

        # Test the resource function also gets hot-reloaded URLs
        with patch("mcp_server_docy.server.settings", settings):
            result3 = list_documentation_sources()
            parsed3 = json.loads(result3.split("\n", 1)[1])
            assert len(parsed3) == 3
            urls3 = [item["url"] for item in parsed3]
            assert "https://updated1.example.com/" in urls3
            assert "https://updated2.example.com/" in urls3
            assert "https://updated3.example.com/" in urls3

        # Test the prompt function also gets hot-reloaded URLs
        with patch("mcp_server_docy.server.settings", settings):
            result4 = documentation_sources()
            # Extract the JSON part from the response
            json_part = result4.split("Here they are:\n", 1)[1]
            parsed4 = json.loads(json_part)
            assert len(parsed4) == 3
            urls4 = [item["url"] for item in parsed4]
            assert "https://updated1.example.com/" in urls4
            assert "https://updated2.example.com/" in urls4
            assert "https://updated3.example.com/" in urls4

    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if "DOCY_DOCUMENTATION_URLS_FILE" in os.environ:
            del os.environ["DOCY_DOCUMENTATION_URLS_FILE"]
