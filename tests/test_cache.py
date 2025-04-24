import asyncio
import os
import shutil
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from diskcache import Cache
from mcp_server_docy.server import (
    async_cached,
    fetch_documentation_content,
    cached_fetch_documentation_content,
    fetch_document_links,
    fetch_documentation_page,
)


@pytest.fixture
def mock_crawler_result():
    """Mock the crawler result for testing."""
    result = MagicMock()
    result.success = True
    result.markdown = "# Test markdown content"
    result.metadata = {"title": "Test Title"}
    result.links = {
        "internal": [{"href": "/internal-link", "text": "Internal Link"}],
        "external": [{"href": "https://external-link", "text": "External Link"}],
    }
    return result


@pytest.fixture
def mock_complex_crawler_result():
    """Mock a more complex crawler result with object attributes."""

    class MockMarkdownResult:
        def __init__(self):
            self.markdown_with_citations = "# Test markdown with citations"
            self.raw_markdown = "# Test raw markdown"

    result = MagicMock()
    result.success = True
    result.markdown = MockMarkdownResult()
    result.metadata = {"title": "Complex Test"}
    result.links = {
        "internal": [{"href": "/internal-link", "text": "Internal Link"}],
        "external": [{"href": "https://external-link", "text": "External Link"}],
    }
    return result


@pytest.fixture
def setup_test_cache():
    """Setup a test cache and clean it up after tests."""
    test_cache_dir = ".test_cache"

    # Clear any existing test cache
    if os.path.exists(test_cache_dir):
        shutil.rmtree(test_cache_dir)

    # Create a new cache
    cache = Cache(test_cache_dir)

    yield cache

    # Clean up after test
    cache.close()
    if os.path.exists(test_cache_dir):
        shutil.rmtree(test_cache_dir)


@pytest.mark.asyncio
async def test_fetch_documentation_content(mock_crawler_result):
    """Test that fetch_documentation_content works correctly with mocked data."""
    url = "https://test-docs.example.com"

    with patch("mcp_server_docy.server.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler_class.return_value.__aenter__.return_value = mock_crawler
        mock_crawler.arun.return_value = mock_crawler_result

        result = await fetch_documentation_content(url)

        assert result["url"] == url
        assert result["title"] == "Test Title"
        assert result["markdown"] == "# Test markdown content"
        assert "links" in result
        assert result["success"] is True


@pytest.mark.asyncio
async def test_fetch_documentation_content_complex_result(mock_complex_crawler_result):
    """Test fetch_documentation_content with complex markdown object."""
    url = "https://test-docs.example.com"

    with patch("mcp_server_docy.server.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler_class.return_value.__aenter__.return_value = mock_crawler
        mock_crawler.arun.return_value = mock_complex_crawler_result

        result = await fetch_documentation_content(url)

        assert result["url"] == url
        assert result["title"] == "Complex Test"
        assert result["markdown"] == "# Test markdown with citations"
        assert "links" in result
        assert result["success"] is True


@pytest.mark.asyncio
async def test_fetch_documentation_page(mock_crawler_result):
    """Test fetch_documentation_page tool function."""
    url = "https://test-docs.example.com"

    with patch("mcp_server_docy.server.fetch_documentation_content") as mock_fetch:
        mock_fetch.return_value = {
            "url": url,
            "title": "Test Title",
            "markdown": "# Test markdown content",
            "links": mock_crawler_result.links,
            "success": True,
        }

        result = await fetch_documentation_page(url)

        assert "# Test Title" in result
        assert "# Test markdown content" in result


@pytest.mark.asyncio
async def test_fetch_document_links(mock_crawler_result):
    """Test fetch_document_links tool function."""
    url = "https://test-docs.example.com"

    with patch("mcp_server_docy.server.fetch_documentation_content") as mock_fetch:
        mock_fetch.return_value = {
            "url": url,
            "title": "Test Title",
            "markdown": "# Test markdown content",
            "links": mock_crawler_result.links,
            "success": True,
        }

        result = await fetch_document_links(url)

        assert "Links extracted from https://test-docs.example.com" in result
        assert "Internal Links (1)" in result
        assert "External Links (1)" in result
        assert "- [Internal Link](/internal-link)" in result
        assert "- [External Link](https://external-link)" in result


def test_async_cached_decorator(setup_test_cache):
    """Test the async_cached decorator with the test cache."""
    cache = setup_test_cache

    # Define a test async function that increments a counter each time it's called
    call_count = 0

    @async_cached
    async def test_func(param):
        nonlocal call_count
        call_count += 1
        return f"Result for {param}, call {call_count}"

    # Mock the cache globally
    with patch("mcp_server_docy.server.cache", cache):
        # Run the function twice with the same parameter - should only increment once
        result1 = asyncio.run(test_func("test"))
        result2 = asyncio.run(test_func("test"))

        # Should be the same result
        assert result1 == result2
        # Function should only have been called once
        assert call_count == 1

        # Run with a different parameter - should increment
        result3 = asyncio.run(test_func("different"))

        # Should be a different result
        assert result3 != result1
        # Function should have been called again
        assert call_count == 2


@pytest.mark.asyncio
async def test_cached_fetch_document_links(setup_test_cache, mock_crawler_result):
    """Test caching behavior for fetch_document_links."""
    cache = setup_test_cache
    url = "https://test-docs.example.com"

    # Mock the function that actually gets the data
    call_count = 0

    async def mock_fetch(test_url):
        nonlocal call_count
        call_count += 1
        return {
            "url": test_url,
            "title": "Test Title",
            "markdown": "# Test markdown content",
            "links": mock_crawler_result.links,
            "success": True,
        }

    # Patch the cache and the fetch function
    with (
        patch("mcp_server_docy.server.cache", cache),
        patch(
            "mcp_server_docy.server.fetch_documentation_content", side_effect=mock_fetch
        ),
    ):
        # First call - should fetch fresh data
        result1 = await fetch_document_links(url)
        assert call_count == 1

        # Second call - should use cached data
        result2 = await fetch_document_links(url)
        # fetch_documentation_content should not be called again
        assert call_count == 1

        # Results should be the same
        assert result1 == result2


@pytest.mark.asyncio
async def test_error_handling_in_cached_functions(setup_test_cache):
    """Test error handling in cached functions."""
    cache = setup_test_cache
    url = "https://test-docs.example.com"

    # Mock fetch_documentation_content to raise an exception
    with (
        patch("mcp_server_docy.server.cache", cache),
        patch(
            "mcp_server_docy.server.fetch_documentation_content",
            side_effect=ValueError("Test error"),
        ),
    ):
        # Should handle the error gracefully
        result = await fetch_document_links(url)

        # Should contain an error message
        assert "Error retrieving links" in result
        assert "Test error" in result


@pytest.mark.asyncio
async def test_cached_fetch_documentation_content(
    setup_test_cache, mock_crawler_result
):
    """Test caching behavior for cached_fetch_documentation_content."""
    cache = setup_test_cache
    url = "https://test-docs.example.com"

    # Mock the function that actually gets the data
    call_count = 0

    async def mock_fetch(test_url):
        nonlocal call_count
        call_count += 1
        return {
            "url": test_url,
            "title": "Test Title",
            "markdown": "# Test markdown content",
            "links": mock_crawler_result.links,
            "success": True,
        }

    # Patch the cache and the fetch function
    with (
        patch("mcp_server_docy.server.cache", cache),
        patch(
            "mcp_server_docy.server.fetch_documentation_content", side_effect=mock_fetch
        ),
    ):
        # First call - should fetch fresh data
        result1 = await cached_fetch_documentation_content(url)
        assert call_count == 1

        # Second call - should use cached data
        result2 = await cached_fetch_documentation_content(url)
        # fetch_documentation_content should not be called again
        assert call_count == 1

        # Results should be the same
        assert result1 == result2


@pytest.mark.asyncio
async def test_cached_complex_object_serialization(
    setup_test_cache, mock_complex_crawler_result
):
    """Test that complex objects are properly serialized and deserialized from cache."""
    cache = setup_test_cache
    url = "https://test-docs.example.com"

    # First mock a successful fetch of complex data
    with (
        patch("mcp_server_docy.server.cache", cache),
        patch("mcp_server_docy.server.AsyncWebCrawler") as mock_crawler_class,
    ):
        # Configure the mock to return complex data
        mock_crawler = AsyncMock()
        mock_crawler_class.return_value.__aenter__.return_value = mock_crawler
        mock_crawler.arun.return_value = mock_complex_crawler_result

        # First call - fetch and cache
        result1 = await fetch_documentation_content(url)

        # Verify the result has the expected format
        assert result1["markdown"] == "# Test markdown with citations"

        # Now fetch again from cache
        result2 = await fetch_documentation_content(url)

        # Should return the same data
        assert result2["markdown"] == "# Test markdown with citations"


@pytest.mark.asyncio
async def test_cached_fetch_links_from_complex_data(
    setup_test_cache, mock_complex_crawler_result
):
    """Test the full flow of fetching links with caching for complex data objects."""
    cache = setup_test_cache
    url = "https://test-docs.example.com"

    call_count = 0

    # Create a mock fetch_documentation_content that increments a counter
    async def mock_fetch(test_url):
        nonlocal call_count
        call_count += 1
        return {
            "url": test_url,
            "title": "Complex Test",
            "markdown": "# Test markdown with citations",
            "links": mock_complex_crawler_result.links,
            "success": True,
        }

    # Patch the cache and functions
    with (
        patch("mcp_server_docy.server.cache", cache),
        patch(
            "mcp_server_docy.server.fetch_documentation_content", side_effect=mock_fetch
        ),
    ):
        # First call - should fetch and cache data
        result1 = await fetch_document_links(url)

        # The links should be in the output
        assert "Internal Links (1)" in result1
        assert call_count == 1

        # Second call - should use cached data
        result2 = await fetch_document_links(url)

        # fetch_documentation_content should not be called again
        assert call_count == 1

        # Results should be the same
        assert result1 == result2


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
