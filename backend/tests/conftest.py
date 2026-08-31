"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import AsyncGenerator
import os
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from datetime import datetime

from backend.models.schemas import (
    CollectorCreate,
    ExtractionLogCreate,
    SelfHealingEventCreate,
    AgentJobCreate,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_firestore():
    """Mock Firestore client."""
    with patch("backend.services.firestore.firestore.AsyncClient") as mock:
        yield mock


@pytest.fixture
async def mock_gemini():
    """Mock Gemini client."""
    with patch("backend.services.gemini.genai") as mock:
        yield mock


@pytest.fixture
def sample_collector_create():
    """Sample collector creation data."""
    return CollectorCreate(
        source_name="Test Knowledge Base",
        target_url="https://example.com",
        css_selectors={
            "title": "h1",
            "content": ".content",
            "updated": ".timestamp",
        },
        cron_schedule="0 * * * *",
        is_active=True,
    )


@pytest.fixture
def sample_extraction_log_create():
    """Sample extraction log creation data."""
    return ExtractionLogCreate(
        collector_id="test-collector-1",
        status="SUCCESS",
        items_extracted=5,
        raw_payload=[
            {"title": "Item 1", "content": "Content 1"},
            {"title": "Item 2", "content": "Content 2"},
        ],
        summary="Successfully extracted 2 items from knowledge base",
    )


@pytest.fixture
def sample_healing_event_create():
    """Sample self-healing event creation data."""
    return SelfHealingEventCreate(
        collector_id="test-collector-1",
        old_selector=".old-selector",
        new_selector=".new-selector",
        confidence_score=0.95,
    )


@pytest.fixture
def sample_agent_job_create():
    """Sample agent job creation data."""
    return AgentJobCreate(
        collector_id="test-collector-1",
        agent_type="COLLECTOR",
        status="PENDING",
        metadata={"task": "extraction", "retry_count": 0},
    )


@pytest.fixture
def unique_id():
    """Generate a unique ID."""
    return f"test-{uuid.uuid4().hex[:8]}"
