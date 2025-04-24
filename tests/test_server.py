import os
import tempfile
from mcp_server_docy.server import Settings, SERVER_NAME


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
