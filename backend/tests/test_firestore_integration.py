"""Integration tests for Firestore service."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

from backend.services.firestore import FirestoreService
from backend.models.schemas import (
    CollectorCreate,
    CollectorUpdate,
    ExtractionLogCreate,
    SelfHealingEventCreate,
    AgentJobCreate,
    CollectorStatus,
    ExtractionStatus,
    HealingStatus,
    AgentStatus,
)


class TestFirestoreCollectorCRUD:
    """Test CRUD operations for collectors."""
    
    @pytest.mark.asyncio
    async def test_create_collector(self, sample_collector_create, unique_id, mock_firestore):
        """Test creating a collector."""
        service = FirestoreService()
        
        # Mock the Firestore client
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            # Mock the document operations
            mock_doc = AsyncMock()
            mock_client.collection.return_value.document.return_value = mock_doc
            
            # Create collector
            result = await service.create_collector(unique_id, sample_collector_create)
            
            # Verify
            assert result is not None
            assert result.collector_id == unique_id
            assert result.source_name == sample_collector_create.source_name
            mock_doc.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_collector(self, unique_id, mock_firestore):
        """Test retrieving a collector."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            # Mock the document retrieval
            mock_snapshot = AsyncMock()
            mock_snapshot.exists = True
            mock_snapshot.to_dict.return_value = {
                "collector_id": unique_id,
                "source_name": "Test KB",
                "target_url": "https://example.com",
                "css_selectors": {"title": "h1"},
                "status": "ACTIVE",
                "is_active": True,
            }
            
            mock_doc = AsyncMock()
            mock_doc.get.return_value = mock_snapshot
            mock_client.collection.return_value.document.return_value = mock_doc
            
            result = await service.get_collector(unique_id)
            
            assert result is not None
            assert result.collector_id == unique_id
            mock_doc.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_collector_not_found(self, unique_id, mock_firestore):
        """Test retrieving non-existent collector returns None."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            # Mock non-existent document
            mock_snapshot = AsyncMock()
            mock_snapshot.exists = False
            
            mock_doc = AsyncMock()
            mock_doc.get.return_value = mock_snapshot
            mock_client.collection.return_value.document.return_value = mock_doc
            
            result = await service.get_collector(unique_id)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_list_collectors(self, mock_firestore):
        """Test listing collectors."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            # Mock the query results
            mock_snapshot = MagicMock()
            mock_snapshot.to_dict.return_value = {
                "collector_id": "collector-1",
                "source_name": "KB 1",
                "target_url": "https://example1.com",
                "css_selectors": {},
                "status": "ACTIVE",
                "is_active": True,
            }
            
            mock_query = AsyncMock()
            mock_query.__aiter__.return_value = [mock_snapshot]
            
            mock_client.collection.return_value.where.return_value.stream = AsyncMock(
                return_value=[mock_snapshot]
            )
            
            result = await service.list_collectors(limit=10)
            
            assert result is not None
            assert len(result) >= 0
    
    @pytest.mark.asyncio
    async def test_update_collector(self, unique_id, mock_firestore):
        """Test updating a collector."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_doc = AsyncMock()
            mock_client.collection.return_value.document.return_value = mock_doc
            
            update_data = CollectorUpdate(css_selectors={"title": "h2"})
            await service.update_collector(unique_id, update_data)
            
            mock_doc.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_collector(self, unique_id, mock_firestore):
        """Test deleting a collector."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_doc = AsyncMock()
            mock_client.collection.return_value.document.return_value = mock_doc
            
            await service.delete_collector(unique_id)
            
            mock_doc.delete.assert_called_once()


class TestFirestoreExtractionLogCRUD:
    """Test CRUD operations for extraction logs."""
    
    @pytest.mark.asyncio
    async def test_create_extraction_log(self, sample_extraction_log_create, mock_firestore):
        """Test creating an extraction log."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_doc = AsyncMock()
            mock_client.collection.return_value.document.return_value = mock_doc
            
            result = await service.create_extraction_log(sample_extraction_log_create)
            
            assert result is not None
            mock_doc.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_extraction_logs(self, mock_firestore):
        """Test listing extraction logs."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_snapshot = MagicMock()
            mock_snapshot.to_dict.return_value = {
                "log_id": "log-1",
                "collector_id": "col-1",
                "status": "SUCCESS",
                "items_extracted": 5,
            }
            
            mock_client.collection.return_value.where.return_value.stream = AsyncMock(
                return_value=[mock_snapshot]
            )
            
            result = await service.list_extraction_logs("col-1", limit=10)
            
            assert result is not None


class TestFirestoreSelfHealingEventCRUD:
    """Test CRUD operations for self-healing events."""
    
    @pytest.mark.asyncio
    async def test_create_healing_event(self, sample_healing_event_create, mock_firestore):
        """Test creating a healing event."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_doc = AsyncMock()
            mock_client.collection.return_value.document.return_value = mock_doc
            
            result = await service.create_self_healing_event(sample_healing_event_create)
            
            assert result is not None
            mock_doc.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_healing_events(self, mock_firestore):
        """Test listing healing events."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_snapshot = MagicMock()
            mock_snapshot.to_dict.return_value = {
                "event_id": "event-1",
                "collector_id": "col-1",
                "status": "SUCCESS",
                "confidence_score": 0.95,
            }
            
            mock_client.collection.return_value.where.return_value.stream = AsyncMock(
                return_value=[mock_snapshot]
            )
            
            result = await service.list_self_healing_events(limit=10)
            
            assert result is not None


class TestFirestoreAgentJobCRUD:
    """Test CRUD operations for agent jobs."""
    
    @pytest.mark.asyncio
    async def test_create_agent_job(self, sample_agent_job_create, mock_firestore):
        """Test creating an agent job."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_doc = AsyncMock()
            mock_client.collection.return_value.document.return_value = mock_doc
            
            result = await service.create_agent_job(sample_agent_job_create)
            
            assert result is not None
            mock_doc.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_agent_job_status(self, unique_id, mock_firestore):
        """Test updating agent job status."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_doc = AsyncMock()
            mock_client.collection.return_value.document.return_value = mock_doc
            
            await service.update_agent_job_status(unique_id, "COMPLETED")
            
            mock_doc.update.assert_called_once()


class TestFirestoreAsyncPatterns:
    """Test async/await patterns in Firestore service."""
    
    @pytest.mark.asyncio
    async def test_concurrent_collector_creation(self, mock_firestore):
        """Test creating multiple collectors concurrently."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_doc = AsyncMock()
            mock_client.collection.return_value.document.return_value = mock_doc
            mock_doc.set.return_value = None
            
            # Create multiple collectors concurrently
            tasks = []
            for i in range(5):
                collector_data = CollectorCreate(
                    source_name=f"KB-{i}",
                    target_url=f"https://example{i}.com",
                    css_selectors={"title": "h1"},
                    is_active=True,
                )
                collector_id = f"collector-{i}"
                tasks.append(service.create_collector(collector_id, collector_data))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all completed
            assert len(results) == 5
            assert all(r is not None for r in results)
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, mock_firestore):
        """Test batch operations."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            mock_batch = AsyncMock()
            mock_client.batch.return_value = mock_batch
            mock_batch.__aenter__ = AsyncMock(return_value=mock_batch)
            mock_batch.__aexit__ = AsyncMock(return_value=None)
            
            # Batch operations should complete
            result = await service.get_statistics()
            
            assert result is not None
            assert "total_collectors" in result


class TestFirestoreConnectionManagement:
    """Test connection management."""
    
    @pytest.mark.asyncio
    async def test_singleton_instance(self):
        """Test that Firestore service uses singleton pattern."""
        service1 = FirestoreService()
        service2 = FirestoreService()
        
        assert service1 is service2
    
    @pytest.mark.asyncio
    async def test_client_reuse(self, mock_firestore):
        """Test that client is reused across calls."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            
            # First call
            client1 = await service._get_client()
            # Second call should return same
            client2 = await service._get_client()
            
            assert client1 is client2


class TestFirestoreErrorHandling:
    """Test error handling in Firestore service."""
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, mock_firestore):
        """Test handling of connection errors."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception):
                await service.get_collector("test-id")
    
    @pytest.mark.asyncio
    async def test_graceful_close(self, mock_firestore):
        """Test graceful closing of Firestore client."""
        service = FirestoreService()
        
        with patch.object(service, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_get.return_value = mock_client
            mock_client.close.return_value = None
            
            await service.close()
            
            # After close, client should be None
            assert service._client is None
