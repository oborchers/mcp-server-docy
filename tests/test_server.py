from mcp_server_docy.server import Settings, SERVER_NAME


def test_settings():
    """Test that the Settings class can be instantiated."""
    settings = Settings()
    assert settings.user_agent.startswith("ModelContextProtocol")


def test_server_metadata():
    """Test server metadata constants."""
    assert SERVER_NAME == "Docy"
