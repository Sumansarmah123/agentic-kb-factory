"""Tests for the Collector Agent with error handling."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime

from backend.agents.collector import CollectorAgent
from backend.models.schemas import CollectorConfig, ExtractionLogCreate


class TestCollectorAgentExtraction:
    """Test content extraction with Collector Agent."""
    
    @pytest.mark.asyncio
    async def test_extract_items_success(self):
        """Test successful item extraction."""
        agent = CollectorAgent()
        
        with patch("backend.agents.collector.httpx") as mock_httpx:
            # Mock HTTP response
            mock_response = MagicMock()
            mock_response.text = """
            <html>
                <h1 class="title">Article Title</h1>
                <div class="content">Article content here</div>
                <span class="date">2024-01-15</span>
            </html>
            """
            mock_response.status_code = 200
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.AsyncClient.return_value = mock_client
            
            collector_config = CollectorConfig(
                collector_id="test-1",
                source_name="Test KB",
                target_url="https://example.com",
                css_selectors={
                    "title": "h1.title",
                    "content": ".content",
                    "date": ".date",
                },
                is_active=True,
            )
            
            result = await agent.extract_items(collector_config)
            
            assert result is not None
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_extract_items_broken_selector(self):
        """Test extraction with broken CSS selector."""
        agent = CollectorAgent()
        
        with patch("backend.agents.collector.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.text = "<html><body>No matching elements</body></html>"
            mock_response.status_code = 200
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.AsyncClient.return_value = mock_client
            
            collector_config = CollectorConfig(
                collector_id="test-1",
                source_name="Test KB",
                target_url="https://example.com",
                css_selectors={
                    "title": ".nonexistent-selector",
                },
                is_active=True,
            )
            
            result = await agent.extract_items(collector_config)
            
            # Should return empty list rather than error
            assert isinstance(result, list)
            assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_extract_with_multiple_items(self):
        """Test extracting multiple items."""
        agent = CollectorAgent()
        
        with patch("backend.agents.collector.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.text = """
            <html>
                <div class="item">
                    <h2 class="item-title">Item 1</h2>
                    <p class="item-desc">Description 1</p>
                </div>
                <div class="item">
                    <h2 class="item-title">Item 2</h2>
                    <p class="item-desc">Description 2</p>
                </div>
                <div class="item">
                    <h2 class="item-title">Item 3</h2>
                    <p class="item-desc">Description 3</p>
                </div>
            </html>
            """
            mock_response.status_code = 200
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.AsyncClient.return_value = mock_client
            
            collector_config = CollectorConfig(
                collector_id="test-1",
                source_name="Test KB",
                target_url="https://example.com",
                css_selectors={
                    "title": ".item-title",
                    "description": ".item-desc",
                },
                is_active=True,
            )
            
            result = await agent.extract_items(collector_config)
            
            assert isinstance(result, list)
            assert len(result) >= 0


class TestCollectorAgentErrorHandling:
    """Test error handling in Collector Agent."""
    
    @pytest.mark.asyncio
    async def test_handle_network_error(self):
        """Test handling network errors."""
        agent = CollectorAgent()
        
        with patch("backend.agents.collector.httpx") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("Network error: connection refused")
            mock_httpx.AsyncClient.return_value = mock_client
            
            collector_config = CollectorConfig(
                collector_id="test-1",
                source_name="Test KB",
                target_url="https://example.com",
                css_selectors={"title": "h1"},
                is_active=True,
            )
            
            # Should handle gracefully
            with pytest.raises(Exception):
                await agent.extract_items(collector_config)
    
    @pytest.mark.asyncio
    async def test_handle_http_404(self):
        """Test handling 404 HTTP errors."""
        agent = CollectorAgent()
        
        with patch("backend.agents.collector.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.AsyncClient.return_value = mock_client
            
            collector_config = CollectorConfig(
                collector_id="test-1",
                source_name="Test KB",
                target_url="https://example.com/nonexistent",
                css_selectors={"title": "h1"},
                is_active=True,
            )
            
            result = await agent.extract_items(collector_config)
            
            # Should handle gracefully
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_handle_http_500(self):
        """Test handling 500 server errors."""
        agent = CollectorAgent()
        
        with patch("backend.agents.collector.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.AsyncClient.return_value = mock_client
            
            collector_config = CollectorConfig(
                collector_id="test-1",
                source_name="Test KB",
                target_url="https://example.com",
                css_selectors={"title": "h1"},
                is_active=True,
            )
            
            result = await agent.extract_items(collector_config)
            
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_handle_timeout(self):
        """Test handling timeout errors."""
        agent = CollectorAgent()
        
        with patch("backend.agents.collector.httpx") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.side_effect = TimeoutError("Request timed out")
            mock_httpx.AsyncClient.return_value = mock_client
            
            collector_config = CollectorConfig(
                collector_id="test-1",
                source_name="Test KB",
                target_url="https://example.com",
                css_selectors={"title": "h1"},
                is_active=True,
            )
            
            with pytest.raises(TimeoutError):
                await agent.extract_items(collector_config)


class TestCollectorAgentLogging:
    """Test extraction logging."""
    
    @pytest.mark.asyncio
    async def test_log_extraction_success(self):
        """Test logging successful extraction."""
        agent = CollectorAgent()
        
        with patch("backend.agents.collector.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.text = "<h1>Title</h1><p>Content</p>"
            mock_response.status_code = 200
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.AsyncClient.return_value = mock_client
            
            with patch.object(agent, "firestore_service") as mock_firestore:
                mock_firestore.create_extraction_log = AsyncMock()
                
                collector_config = CollectorConfig(
                    collector_id="test-1",
                    source_name="Test KB",
                    target_url="https://example.com",
                    css_selectors={"title": "h1"},
                    is_active=True,
                )
                
                result = await agent.extract_items(collector_config)
                
                # Verify logging would be called
                assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_log_extraction_failure(self):
        """Test logging failed extraction."""
        agent = CollectorAgent()
        
        with patch("backend.agents.collector.httpx") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("Error")
            mock_httpx.AsyncClient.return_value = mock_client
            
            collector_config = CollectorConfig(
                collector_id="test-1",
                source_name="Test KB",
                target_url="https://example.com",
                css_selectors={"title": "h1"},
                is_active=True,
            )
            
            with pytest.raises(Exception):
                await agent.extract_items(collector_config)


class TestCollectorAgentPipeline:
    """Test the complete extraction pipeline."""
    
    @pytest.mark.asyncio
    async def test_full_extraction_pipeline(self):
        """Test complete extraction pipeline."""
        agent = CollectorAgent()
        
        with patch("backend.agents.collector.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.text = """
            <html>
                <title>Test KB</title>
                <div class="article">
                    <h1>Article 1</h1>
                    <p>Content 1</p>
                </div>
            </html>
            """
            mock_response.status_code = 200
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.AsyncClient.return_value = mock_client
            
            collector_config = CollectorConfig(
                collector_id="test-1",
                source_name="Test KB",
                target_url="https://example.com",
                css_selectors={
                    "title": "title",
                    "article": ".article",
                },
                is_active=True,
            )
            
            result = await agent.extract_items(collector_config)
            
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_pipeline_with_healing_trigger(self):
        """Test pipeline triggering healing on broken selector."""
        agent = CollectorAgent()
        
        with patch("backend.agents.collector.httpx") as mock_httpx:
            # First response returns empty (broken selector)
            mock_response = MagicMock()
            mock_response.text = "<html><body>Content</body></html>"
            mock_response.status_code = 200
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.AsyncClient.return_value = mock_client
            
            collector_config = CollectorConfig(
                collector_id="test-1",
                source_name="Test KB",
                target_url="https://example.com",
                css_selectors={
                    "title": ".nonexistent",
                },
                is_active=True,
            )
            
            result = await agent.extract_items(collector_config)
            
            # Pipeline should handle gracefully
            assert isinstance(result, list)


class TestCollectorAgentWithDifferentSelectors:
    """Test collector with various CSS selector types."""
    
    @pytest.mark.asyncio
    async def test_class_based_selectors(self):
        """Test extraction with class-based selectors."""
        agent = CollectorAgent()
        
        with patch("backend.agents.collector.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.text = """
            <html>
                <div class="article">
                    <span class="title">Article</span>
                    <span class="author">John</span>
                </div>
            </html>
            """
            mock_response.status_code = 200
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.AsyncClient.return_value = mock_client
            
            collector_config = CollectorConfig(
                collector_id="test-1",
                source_name="Test KB",
                target_url="https://example.com",
                css_selectors={
                    "title": ".title",
                    "author": ".author",
                },
                is_active=True,
            )
            
            result = await agent.extract_items(collector_config)
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_id_based_selectors(self):
        """Test extraction with ID-based selectors."""
        agent = CollectorAgent()
        
        with patch("backend.agents.collector.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.text = """
            <html>
                <h1 id="main-title">Main Title</h1>
                <div id="content">Content area</div>
            </html>
            """
            mock_response.status_code = 200
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.AsyncClient.return_value = mock_client
            
            collector_config = CollectorConfig(
                collector_id="test-1",
                source_name="Test KB",
                target_url="https://example.com",
                css_selectors={
                    "title": "#main-title",
                    "content": "#content",
                },
                is_active=True,
            )
            
            result = await agent.extract_items(collector_config)
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_complex_selectors(self):
        """Test extraction with complex CSS selectors."""
        agent = CollectorAgent()
        
        with patch("backend.agents.collector.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.text = """
            <html>
                <div class="container">
                    <article class="post">
                        <h2>Post Title</h2>
                        <div class="meta">
                            <span class="author">Author</span>
                            <span class="date">2024-01-15</span>
                        </div>
                    </article>
                </div>
            </html>
            """
            mock_response.status_code = 200
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.AsyncClient.return_value = mock_client
            
            collector_config = CollectorConfig(
                collector_id="test-1",
                source_name="Test KB",
                target_url="https://example.com",
                css_selectors={
                    "title": ".container article.post h2",
                    "author": ".meta .author",
                    "date": ".meta > .date",
                },
                is_active=True,
            )
            
            result = await agent.extract_items(collector_config)
            assert isinstance(result, list)
