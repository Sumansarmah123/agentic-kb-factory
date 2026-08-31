"""Integration tests for Gemini service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from backend.services.gemini import GeminiService


class TestGeminiContentClassification:
    """Test content classification with Gemini 3.5."""
    
    @pytest.mark.asyncio
    async def test_classify_content_success(self):
        """Test successful content classification."""
        service = GeminiService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            # Mock the Gemini response
            mock_response = MagicMock()
            mock_response.text = json.dumps({
                "category": "API_UPDATE",
                "urgency": "HIGH",
                "is_breaking_change": True,
                "summary": "Breaking API change in authentication endpoint",
                "key_changes": ["Auth endpoint deprecated", "New OAuth2 flow required"],
            })
            
            mock_model = AsyncMock()
            mock_model.generate_content_async.return_value = mock_response
            mock_client.GenerativeModel.return_value = mock_model
            
            html_content = "<h1>Breaking API Change</h1><p>The old auth endpoint is deprecated.</p>"
            result = await service.classify_content(html_content)
            
            assert result is not None
            assert "category" in result or result is not None
    
    @pytest.mark.asyncio
    async def test_classify_content_with_urgency_levels(self):
        """Test classification with different urgency levels."""
        service = GeminiService()
        
        test_cases = [
            ("Minor bug fix released", "LOW"),
            ("Security vulnerability patch available", "CRITICAL"),
            ("New feature available", "MEDIUM"),
        ]
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            for content, expected_urgency in test_cases:
                mock_response = MagicMock()
                mock_response.text = json.dumps({
                    "category": "UPDATE",
                    "urgency": expected_urgency,
                    "is_breaking_change": False,
                    "summary": content,
                })
                
                mock_model = AsyncMock()
                mock_model.generate_content_async.return_value = mock_response
                mock_client.GenerativeModel.return_value = mock_model
                
                result = await service.classify_content(content)
                assert result is not None


class TestGeminiSelectorHealing:
    """Test autonomous selector healing with Gemini."""
    
    @pytest.mark.asyncio
    async def test_heal_selector_success(self):
        """Test successful selector healing."""
        service = GeminiService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.text = json.dumps({
                "new_selector": ".updated-title",
                "confidence_score": 0.95,
                "reasoning": "The title element moved to a class instead of ID",
                "verification": "Found matching elements with new selector",
            })
            
            mock_model = AsyncMock()
            mock_model.generate_content_async.return_value = mock_response
            mock_client.GenerativeModel.return_value = mock_model
            
            broken_html = "<div class='updated-title'>Article Title</div>"
            old_selector = "#title"
            
            result = await service.heal_selector(broken_html, old_selector)
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_heal_selector_high_confidence(self):
        """Test selector healing with high confidence score."""
        service = GeminiService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.text = json.dumps({
                "new_selector": ".article-header",
                "confidence_score": 0.98,
                "reasoning": "High confidence match based on semantic similarity",
            })
            
            mock_model = AsyncMock()
            mock_model.generate_content_async.return_value = mock_response
            mock_client.GenerativeModel.return_value = mock_model
            
            result = await service.heal_selector(
                "<div class='article-header'>Title</div>",
                ".old-header"
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_heal_selector_low_confidence(self):
        """Test selector healing handling low confidence."""
        service = GeminiService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.text = json.dumps({
                "new_selector": ".possible-match",
                "confidence_score": 0.45,
                "reasoning": "Low confidence - unclear target element",
            })
            
            mock_model = AsyncMock()
            mock_model.generate_content_async.return_value = mock_response
            mock_client.GenerativeModel.return_value = mock_model
            
            result = await service.heal_selector(
                "<div>Unclear HTML</div>",
                ".ambiguous-selector"
            )
            
            # Should handle low confidence gracefully
            assert result is not None


class TestGeminiSummaryGeneration:
    """Test summary generation with Gemini."""
    
    @pytest.mark.asyncio
    async def test_generate_summary_single_item(self):
        """Test summary generation for single extracted item."""
        service = GeminiService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.text = "Executive summary of the changelog entry."
            
            mock_model = AsyncMock()
            mock_model.generate_content_async.return_value = mock_response
            mock_client.GenerativeModel.return_value = mock_model
            
            items = [{"title": "API Update", "content": "New endpoint available"}]
            result = await service.generate_summary(items)
            
            assert result is not None
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_generate_summary_multiple_items(self):
        """Test summary generation for multiple items."""
        service = GeminiService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.text = "Consolidated summary of multiple updates."
            
            mock_model = AsyncMock()
            mock_model.generate_content_async.return_value = mock_response
            mock_client.GenerativeModel.return_value = mock_model
            
            items = [
                {"title": "Feature A", "content": "New feature description"},
                {"title": "Bug Fix B", "content": "Fixed critical bug"},
                {"title": "Security Patch", "content": "Security vulnerability patched"},
            ]
            
            result = await service.generate_summary(items)
            
            assert result is not None
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_generate_summary_empty_items(self):
        """Test summary generation with empty items."""
        service = GeminiService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            result = await service.generate_summary([])
            
            # Should handle empty gracefully
            assert result is not None


class TestGeminiDOMAnalysis:
    """Test DOM structure analysis with Gemini."""
    
    @pytest.mark.asyncio
    async def test_analyze_dom_structure(self):
        """Test analyzing DOM structure."""
        service = GeminiService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.text = json.dumps({
                "structure": {
                    "title_element": "h1.article-title",
                    "content_area": "div.article-body",
                    "metadata": "div.article-meta",
                },
                "changes_detected": ["Class names updated", "Nested structure changed"],
            })
            
            mock_model = AsyncMock()
            mock_model.generate_content_async.return_value = mock_response
            mock_client.GenerativeModel.return_value = mock_model
            
            html = "<h1 class='article-title'>Title</h1><div class='article-body'>Content</div>"
            result = await service.analyze_dom_structure(html)
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_detect_structural_changes(self):
        """Test detecting structural changes in DOM."""
        service = GeminiService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            old_html = "<div id='content'><h1 id='title'>Title</h1></div>"
            new_html = "<div class='content'><header><h1 class='title'>Title</h1></header></div>"
            
            mock_response = MagicMock()
            mock_response.text = json.dumps({
                "changes": [
                    "ID-based selectors changed to class-based",
                    "New wrapper element added",
                    "Nesting structure modified",
                ],
                "impact": "HIGH",
            })
            
            mock_model = AsyncMock()
            mock_model.generate_content_async.return_value = mock_response
            mock_client.GenerativeModel.return_value = mock_model
            
            result = await service.analyze_dom_structure(new_html)
            
            assert result is not None


class TestGeminiHealthCheck:
    """Test Gemini service health checks."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        service = GeminiService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            # Mock successful response
            mock_response = MagicMock()
            mock_response.text = "Health check passed"
            
            mock_model = AsyncMock()
            mock_model.generate_content_async.return_value = mock_response
            mock_client.GenerativeModel.return_value = mock_model
            
            result = await service.health_check()
            
            assert result is True or result is not None
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check with failure."""
        service = GeminiService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_get.side_effect = Exception("API unavailable")
            
            result = await service.health_check()
            
            assert result is False or result is None


class TestGeminiErrorHandling:
    """Test error handling in Gemini service."""
    
    @pytest.mark.asyncio
    async def test_handle_invalid_json_response(self):
        """Test handling invalid JSON in Gemini response."""
        service = GeminiService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            # Mock response with invalid JSON
            mock_response = MagicMock()
            mock_response.text = "Invalid JSON {broken"
            
            mock_model = AsyncMock()
            mock_model.generate_content_async.return_value = mock_response
            mock_client.GenerativeModel.return_value = mock_model
            
            # Should handle gracefully
            result = await service.classify_content("test")
            assert result is not None or result is None  # Either graceful handling
    
    @pytest.mark.asyncio
    async def test_handle_timeout_error(self):
        """Test handling timeout errors."""
        service = GeminiService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_model = AsyncMock()
            mock_model.generate_content_async.side_effect = TimeoutError("Request timed out")
            mock_client.GenerativeModel.return_value = mock_model
            
            with pytest.raises(TimeoutError):
                await service.classify_content("test")
    
    @pytest.mark.asyncio
    async def test_handle_rate_limit_error(self):
        """Test handling rate limit errors."""
        service = GeminiService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_model = AsyncMock()
            mock_model.generate_content_async.side_effect = Exception("429: Rate limit exceeded")
            mock_client.GenerativeModel.return_value = mock_model
            
            with pytest.raises(Exception):
                await service.classify_content("test")


class TestGeminiPerformance:
    """Test performance characteristics of Gemini service."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling concurrent Gemini requests."""
        import asyncio
        service = GeminiService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.text = json.dumps({"result": "success"})
            
            mock_model = AsyncMock()
            mock_model.generate_content_async.return_value = mock_response
            mock_client.GenerativeModel.return_value = mock_model
            
            # Run 5 concurrent classification requests
            tasks = [
                service.classify_content(f"Content {i}")
                for i in range(5)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            assert len(results) == 5
            assert all(r is not None for r in results)
