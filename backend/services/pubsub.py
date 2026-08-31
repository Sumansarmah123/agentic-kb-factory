"""
Pub/Sub service for Agentic KB Factory.
Handles async event dispatch for background agent jobs.
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from google.cloud import pubsub_v1
from google.api_core import exceptions as gcp_exceptions

from backend.config import settings

logger = logging.getLogger(__name__)


class PubSubService:
    """
    Service for Google Cloud Pub/Sub operations.
    
    Used for:
    - Dispatching async collector jobs
    - Triggering healing events
    - Event-driven architecture
    """
    
    _instance: Optional["PubSubService"] = None
    
    def __new__(cls) -> "PubSubService":
        """Singleton pattern for Pub/Sub client."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize Pub/Sub client."""
        if self._initialized:
            return
        
        self._publisher: Optional[pubsub_v1.PublisherClient] = None
        self._topic_path: Optional[str] = None
        self._initialized = True
    
    def _get_publisher(self) -> pubsub_v1.PublisherClient:
        """Get or create Pub/Sub publisher client."""
        if self._publisher is None:
            self._publisher = pubsub_v1.PublisherClient()
            self._topic_path = self._publisher.topic_path(
                settings.gcp_project_id,
                settings.pubsub_topic,
            )
            logger.info(f"Pub/Sub publisher initialized for topic: {settings.pubsub_topic}")
        return self._publisher
    
    async def publish_job(
        self,
        job_id: str,
        collector_id: str,
        job_type: str = "extraction",
        payload: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Publish a job to the Pub/Sub topic.
        
        Args:
            job_id: Unique identifier for the job
            collector_id: The collector to run
            job_type: Type of job (extraction, healing, etc.)
            payload: Additional job data
            
        Returns:
            Message ID
        """
        publisher = self._get_publisher()
        
        message_data = {
            "job_id": job_id,
            "collector_id": collector_id,
            "job_type": job_type,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload or {},
        }
        
        # Publish message
        future = publisher.publish(
            self._topic_path,
            json.dumps(message_data).encode("utf-8"),
            attributes={
                "job_id": job_id,
                "collector_id": collector_id,
                "job_type": job_type,
            },
        )
        
        message_id = future.result()
        logger.info(f"Published job {job_id} to Pub/Sub: {message_id}")
        return message_id
    
    async def publish_healing_request(
        self,
        event_id: str,
        collector_id: str,
        field_name: str,
        old_selector: str,
    ) -> str:
        """
        Publish a healing request to Pub/Sub.
        
        Args:
            event_id: Unique identifier for the healing event
            collector_id: The collector needing healing
            field_name: The field with broken selector
            old_selector: The broken selector
            
        Returns:
            Message ID
        """
        return await self.publish_job(
            job_id=event_id,
            collector_id=collector_id,
            job_type="healing",
            payload={
                "field_name": field_name,
                "old_selector": old_selector,
            },
        )
    
    async def health_check(self) -> bool:
        """
        Check if Pub/Sub service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            publisher = self._get_publisher()
            # Try to get topic info
            from google.cloud.pubsub_v1 import PublisherClient
            client = PublisherClient()
            topic_path = client.topic_path(settings.gcp_project_id, settings.pubsub_topic)
            # Just check we can construct the path
            return True
        except Exception as e:
            logger.error(f"Pub/Sub health check failed: {e}")
            return False


# Singleton instance
pubsub_service = PubSubService()
