"""
Firestore service for Agentic KB Factory.
Handles all database operations for collectors, logs, and healing events.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from google.cloud import firestore
from google.cloud.firestore import AsyncClient, CollectionReference
from google.api_core import exceptions as gcp_exceptions

from backend.config import settings
from backend.models.schemas import (
    CollectorConfig,
    CollectorCreate,
    CollectorUpdate,
    ExtractionLog,
    ExtractionLogCreate,
    SelfHealingEvent,
    SelfHealingEventCreate,
    AgentJob,
    AgentJobCreate,
)

logger = logging.getLogger(__name__)


class FirestoreService:
    """
    Async Firestore service for managing agent state and logs.
    
    Collections:
    - collectors: CollectorConfig documents
    - extraction_logs: ExtractionLog documents
    - healing_events: SelfHealingEvent documents
    - agent_jobs: AgentJob documents
    """
    
    _instance: Optional["FirestoreService"] = None
    
    def __new__(cls) -> "FirestoreService":
        """Singleton pattern for Firestore client."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize Firestore client."""
        if self._initialized:
            return
        
        self._client: Optional[AsyncClient] = None
        self._initialized = True
    
    async def _get_client(self) -> AsyncClient:
        """Get or create async Firestore client."""
        if self._client is None:
            try:
                self._client = firestore.AsyncClient(
                    project=settings.gcp_project_id,
                    database=settings.firestore_database_id,
                )
                logger.info(f"Firestore client initialized for project: {settings.gcp_project_id}")
            except Exception as e:
                logger.error(f"Failed to initialize Firestore client: {e}")
                raise
        return self._client
    
    async def close(self):
        """Close the Firestore client."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Firestore client closed")
    
    # ============================================
    # Collector Operations
    # ============================================
    
    async def create_collector(
        self,
        collector_id: str,
        data: CollectorCreate,
    ) -> CollectorConfig:
        """
        Create a new collector configuration.
        
        Args:
            collector_id: Unique identifier for the collector
            data: Collector creation data
            
        Returns:
            Created CollectorConfig
        """
        client = await self._get_client()
        
        collector = CollectorConfig(
            collector_id=collector_id,
            source_name=data.source_name,
            target_url=data.target_url,
            css_selectors=data.css_selectors,
            cron_schedule=data.cron_schedule,
            is_active=data.is_active,
            metadata=data.metadata or {},
        )
        
        doc_ref = client.collection("collectors").document(collector_id)
        await doc_ref.set(collector.model_dump(mode="json"))
        
        logger.info(f"Created collector: {collector_id}")
        return collector
    
    async def get_collector(self, collector_id: str) -> Optional[CollectorConfig]:
        """
        Get a collector by ID.
        
        Args:
            collector_id: The collector ID
            
        Returns:
            CollectorConfig if found, None otherwise
        """
        client = await self._get_client()
        
        doc_ref = client.collection("collectors").document(collector_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        return CollectorConfig(**data)
    
    async def update_collector(
        self,
        collector_id: str,
        data: CollectorUpdate,
    ) -> Optional[CollectorConfig]:
        """
        Update a collector configuration.
        
        Args:
            collector_id: The collector ID
            data: Update data (only non-None fields are updated)
            
        Returns:
            Updated CollectorConfig if found, None otherwise
        """
        client = await self._get_client()
        
        # Get existing collector
        existing = await self.get_collector(collector_id)
        if not existing:
            return None
        
        # Build update dict (only non-None values)
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        # Update in Firestore
        doc_ref = client.collection("collectors").document(collector_id)
        await doc_ref.update(update_data)
        
        # Return updated collector
        return await self.get_collector(collector_id)
    
    async def delete_collector(self, collector_id: str) -> bool:
        """
        Delete a collector.
        
        Args:
            collector_id: The collector ID
            
        Returns:
            True if deleted, False if not found
        """
        client = await self._get_client()
        
        doc_ref = client.collection("collectors").document(collector_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            return False
        
        await doc_ref.delete()
        logger.info(f"Deleted collector: {collector_id}")
        return True
    
    async def list_collectors(
        self,
        active_only: bool = False,
        limit: int = 100,
    ) -> List[CollectorConfig]:
        """
        List all collectors.
        
        Args:
            active_only: If True, only return active collectors
            limit: Maximum number of results
            
        Returns:
            List of CollectorConfig
        """
        client = await self._get_client()
        
        query = client.collection("collectors")
        
        if active_only:
            query = query.where("is_active", "==", True)
        
        docs = await query.limit(limit).get()
        
        return [CollectorConfig(**doc.to_dict()) for doc in docs]
    
    async def update_collector_status(
        self,
        collector_id: str,
        status: str,
        increment_success: bool = False,
        increment_error: bool = False,
    ) -> None:
        """
        Update collector status after a run.
        
        Args:
            collector_id: The collector ID
            status: New status
            increment_success: Whether to increment success count
            increment_error: Whether to increment error count
        """
        client = await self._get_client()
        
        doc_ref = client.collection("collectors").document(collector_id)
        
        updates = {
            "status": status,
            "last_run": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        if increment_success:
            await doc_ref.update({
                **updates,
                "success_count": firestore.Increment(1),
            })
        elif increment_error:
            await doc_ref.update({
                **updates,
                "error_count": firestore.Increment(1),
            })
        else:
            await doc_ref.update(updates)
    
    # ============================================
    # Extraction Log Operations
    # ============================================
    
    async def log_extraction(
        self,
        log_id: str,
        data: ExtractionLogCreate,
    ) -> ExtractionLog:
        """
        Log an extraction run.
        
        Args:
            log_id: Unique identifier for the log
            data: Extraction log data
            
        Returns:
            Created ExtractionLog
        """
        client = await self._get_client()
        
        log = ExtractionLog(
            log_id=log_id,
            collector_id=data.collector_id,
            status=data.status,
            items_extracted=data.items_extracted,
            raw_payload=data.raw_payload,
            summary=data.summary,
            error_message=data.error_message,
            healing_triggered=data.healing_triggered,
            execution_time_ms=data.execution_time_ms,
        )
        
        doc_ref = client.collection("extraction_logs").document(log_id)
        await doc_ref.set(log.model_dump(mode="json"))
        
        logger.info(f"Logged extraction: {log_id} for collector: {data.collector_id}")
        return log
    
    async def list_extraction_logs(
        self,
        collector_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[ExtractionLog]:
        """
        List extraction logs.
        
        Args:
            collector_id: Filter by collector ID (optional)
            limit: Maximum number of results
            
        Returns:
            List of ExtractionLog
        """
        client = await self._get_client()
        
        query = client.collection("extraction_logs").order_by(
            "timestamp",
            direction=firestore.Query.DESCENDING
        )
        
        if collector_id:
            query = query.where("collector_id", "==", collector_id)
        
        docs = await query.limit(limit).get()
        
        return [ExtractionLog(**doc.to_dict()) for doc in docs]
    
    async def get_latest_extraction_log(
        self,
        collector_id: str,
    ) -> Optional[ExtractionLog]:
        """
        Get the latest extraction log for a collector.
        
        Args:
            collector_id: The collector ID
            
        Returns:
            Latest ExtractionLog if found, None otherwise
        """
        client = await self._get_client()
        
        query = client.collection("extraction_logs").where(
            "collector_id", "==", collector_id
        ).order_by(
            "timestamp",
            direction=firestore.Query.DESCENDING
        ).limit(1)
        
        docs = await query.get()
        
        if not docs:
            return None
        
        return ExtractionLog(**docs[0].to_dict())
    
    # ============================================
    # Self-Healing Event Operations
    # ============================================
    
    async def log_healing_event(
        self,
        event_id: str,
        data: SelfHealingEventCreate,
    ) -> SelfHealingEvent:
        """
        Log a self-healing event.
        
        Args:
            event_id: Unique identifier for the event
            data: Healing event data
            
        Returns:
            Created SelfHealingEvent
        """
        client = await self._get_client()
        
        event = SelfHealingEvent(
            event_id=event_id,
            collector_id=data.collector_id,
            field_name=data.field_name,
            old_selector=data.old_selector,
            new_selector=data.new_selector,
            confidence_score=data.confidence_score,
            status=data.status,
            reasoning=data.reasoning,
        )
        
        doc_ref = client.collection("healing_events").document(event_id)
        await doc_ref.set(event.model_dump(mode="json"))
        
        logger.info(f"Logged healing event: {event_id} for collector: {data.collector_id}")
        return event
    
    async def update_healing_event(
        self,
        event_id: str,
        status: str,
        verified: bool = False,
    ) -> Optional[SelfHealingEvent]:
        """
        Update a healing event status.
        
        Args:
            event_id: The event ID
            status: New status
            verified: Whether the healing was verified
            
        Returns:
            Updated SelfHealingEvent if found, None otherwise
        """
        client = await self._get_client()
        
        doc_ref = client.collection("healing_events").document(event_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            return None
        
        await doc_ref.update({
            "status": status,
            "verified": verified,
        })
        
        doc = await doc_ref.get()
        return SelfHealingEvent(**doc.to_dict())
    
    async def list_healing_events(
        self,
        collector_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[SelfHealingEvent]:
        """
        List self-healing events.
        
        Args:
            collector_id: Filter by collector ID (optional)
            limit: Maximum number of results
            
        Returns:
            List of SelfHealingEvent
        """
        client = await self._get_client()
        
        query = client.collection("healing_events").order_by(
            "timestamp",
            direction=firestore.Query.DESCENDING
        )
        
        if collector_id:
            query = query.where("collector_id", "==", collector_id)
        
        docs = await query.limit(limit).get()
        
        return [SelfHealingEvent(**doc.to_dict()) for doc in docs]
    
    # ============================================
    # Agent Job Operations
    # ============================================
    
    async def create_job(
        self,
        job_id: str,
        data: AgentJobCreate,
    ) -> AgentJob:
        """
        Create a new agent job.
        
        Args:
            job_id: Unique identifier for the job
            data: Job creation data
            
        Returns:
            Created AgentJob
        """
        client = await self._get_client()
        
        job = AgentJob(
            job_id=job_id,
            collector_id=data.collector_id,
            job_type=data.job_type,
            status="pending",
        )
        
        doc_ref = client.collection("agent_jobs").document(job_id)
        await doc_ref.set(job.model_dump(mode="json"))
        
        logger.info(f"Created job: {job_id} for collector: {data.collector_id}")
        return job
    
    async def get_job(self, job_id: str) -> Optional[AgentJob]:
        """
        Get a job by ID.
        
        Args:
            job_id: The job ID
            
        Returns:
            AgentJob if found, None otherwise
        """
        client = await self._get_client()
        
        doc_ref = client.collection("agent_jobs").document(job_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            return None
        
        return AgentJob(**doc.to_dict())
    
    async def update_job_status(
        self,
        job_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[AgentJob]:
        """
        Update job status.
        
        Args:
            job_id: The job ID
            status: New status
            result: Job result (optional)
            error: Error message (optional)
            
        Returns:
            Updated AgentJob if found, None otherwise
        """
        client = await self._get_client()
        
        doc_ref = client.collection("agent_jobs").document(job_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            return None
        
        updates = {"status": status}
        
        if status == "running":
            updates["started_at"] = datetime.utcnow()
        elif status in ("completed", "failed"):
            updates["completed_at"] = datetime.utcnow()
        
        if result:
            updates["result"] = result
        if error:
            updates["error"] = error
        
        await doc_ref.update(updates)
        
        doc = await doc_ref.get()
        return AgentJob(**doc.to_dict())
    
    # ============================================
    # Statistics
    # ============================================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get system statistics.
        
        Returns:
            Dictionary with system stats
        """
        client = await self._get_client()
        
        # Count collectors
        collectors = await self.list_collectors(limit=1000)
        active_collectors = [c for c in collectors if c.is_active]
        
        # Count healing events
        healing_events = await self.list_healing_events(limit=1000)
        successful_heals = [e for e in healing_events if e.status == "success"]
        
        # Count extraction logs
        extraction_logs = await self.list_extraction_logs(limit=1000)
        successful_extractions = [l for l in extraction_logs if l.status == "success"]
        
        return {
            "total_collectors": len(collectors),
            "active_collectors": len(active_collectors),
            "total_healing_events": len(healing_events),
            "successful_heals": len(successful_heals),
            "total_extractions": len(extraction_logs),
            "successful_extractions": len(successful_extractions),
            "healing_success_rate": (
                len(successful_heals) / len(healing_events) * 100
                if healing_events else 0
            ),
            "extraction_success_rate": (
                len(successful_extractions) / len(extraction_logs) * 100
                if extraction_logs else 0
            ),
        }


# Singleton instance
firestore_service = FirestoreService()
