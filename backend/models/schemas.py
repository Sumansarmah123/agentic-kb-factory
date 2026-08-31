"""
Pydantic models for Agentic KB Factory.
Defines schemas for Firestore documents and API responses.
"""

from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================
# Enums
# ============================================

class CollectorStatus(str, Enum):
    """Status of a collector."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    HEALING = "healing"


class ExtractionStatus(str, Enum):
    """Status of an extraction run."""
    SUCCESS = "success"
    FAILED = "failed"
    BROKEN_DOM = "broken_dom"
    HEALING = "healing"


class HealingStatus(str, Enum):
    """Status of a self-healing event."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class HealthStatus(str, Enum):
    """Overall system health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# ============================================
# Collector Configuration
# ============================================

class CollectorConfig(BaseModel):
    """Configuration for a knowledge base collector."""
    
    collector_id: str = Field(..., description="Unique identifier for the collector")
    source_name: str = Field(..., description="Human-readable name of the source")
    target_url: str = Field(..., description="URL to scrape")
    css_selectors: Dict[str, str] = Field(
        default_factory=dict,
        description="CSS selectors for data extraction"
    )
    cron_schedule: str = Field(
        default="0 * * * *",
        description="Cron schedule for automatic runs (hourly by default)"
    )
    is_active: bool = Field(default=True, description="Whether collector is active")
    status: CollectorStatus = Field(
        default=CollectorStatus.ACTIVE,
        description="Current status of the collector"
    )
    last_run: Optional[datetime] = Field(default=None, description="Last run timestamp")
    success_count: int = Field(default=0, description="Number of successful extractions")
    error_count: int = Field(default=0, description="Number of failed extractions")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator("target_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class CollectorCreate(BaseModel):
    """Schema for creating a new collector."""
    source_name: str = Field(..., min_length=1, max_length=200)
    target_url: str = Field(...)
    css_selectors: Dict[str, str] = Field(..., min_length=1)
    cron_schedule: str = Field(default="0 * * * *")
    is_active: bool = Field(default=True)
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class CollectorUpdate(BaseModel):
    """Schema for updating a collector."""
    source_name: Optional[str] = Field(default=None)
    target_url: Optional[str] = Field(default=None)
    css_selectors: Optional[Dict[str, str]] = Field(default=None)
    cron_schedule: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)
    status: Optional[CollectorStatus] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)


# ============================================
# Extraction Log
# ============================================

class ExtractionLog(BaseModel):
    """Log of an extraction run."""
    
    log_id: str = Field(..., description="Unique identifier for the log")
    collector_id: str = Field(..., description="ID of the collector that ran")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Run timestamp")
    status: ExtractionStatus = Field(..., description="Status of the extraction")
    items_extracted: int = Field(default=0, description="Number of items extracted")
    raw_payload: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Raw extracted data"
    )
    summary: str = Field(default="", description="AI-generated summary")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    healing_triggered: bool = Field(default=False, description="Whether healing was triggered")
    execution_time_ms: Optional[int] = Field(default=None, description="Execution time in milliseconds")


class ExtractionLogCreate(BaseModel):
    """Schema for creating an extraction log."""
    collector_id: str
    status: ExtractionStatus
    items_extracted: int = 0
    raw_payload: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str = ""
    error_message: Optional[str] = None
    healing_triggered: bool = False
    execution_time_ms: Optional[int] = None


# ============================================
# Self-Healing Event
# ============================================

class SelfHealingEvent(BaseModel):
    """Record of a self-healing event."""
    
    event_id: str = Field(..., description="Unique identifier for the event")
    collector_id: str = Field(..., description="ID of the collector being healed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    field_name: str = Field(..., description="Name of the field with broken selector")
    old_selector: str = Field(..., description="Previous CSS selector")
    new_selector: str = Field(..., description="New CSS selector")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)"
    )
    status: HealingStatus = Field(default=HealingStatus.PENDING, description="Healing status")
    reasoning: Optional[str] = Field(default=None, description="AI reasoning for the fix")
    dom_snapshot_before: Optional[str] = Field(default=None, description="DOM before healing")
    dom_snapshot_after: Optional[str] = Field(default=None, description="DOM after healing")
    verified: bool = Field(default=False, description="Whether healing was verified successful")


class SelfHealingEventCreate(BaseModel):
    """Schema for creating a self-healing event."""
    collector_id: str
    field_name: str
    old_selector: str
    new_selector: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    status: HealingStatus = HealingStatus.PENDING
    reasoning: Optional[str] = None


# ============================================
# Agent Job
# ============================================

class AgentJob(BaseModel):
    """Represents a job for the agent system."""
    
    job_id: str = Field(..., description="Unique identifier for the job")
    collector_id: str = Field(..., description="ID of the collector")
    job_type: str = Field(default="extraction", description="Type of job")
    status: str = Field(default="pending", description="Job status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Job result")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class AgentJobCreate(BaseModel):
    """Schema for creating an agent job."""
    collector_id: str
    job_type: str = "extraction"


# ============================================
# API Response Models
# ============================================

class HealthCheckResponse(BaseModel):
    """Response for health check endpoint."""
    status: HealthStatus
    app_name: str
    version: str
    gcp_connected: bool
    firestore_connected: bool
    gemini_connected: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CollectorListResponse(BaseModel):
    """Response for list collectors endpoint."""
    collectors: List[CollectorConfig]
    total: int
    active: int
    unhealthy: int


class ExtractionLogListResponse(BaseModel):
    """Response for list extraction logs endpoint."""
    logs: List[ExtractionLog]
    total: int


class HealingLogListResponse(BaseModel):
    """Response for list healing logs endpoint."""
    events: List[SelfHealingEvent]
    total: int
    successful: int
    failed: int


class TriggerRunResponse(BaseModel):
    """Response for triggering a collector run."""
    job_id: str
    collector_id: str
    status: str
    message: str


class ExportDataResponse(BaseModel):
    """Response for export endpoint."""
    collectors: List[CollectorConfig]
    extraction_logs: List[ExtractionLog]
    healing_events: List[SelfHealingEvent]
    exported_at: datetime = Field(default_factory=datetime.utcnow)
