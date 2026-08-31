"""
Orchestrator Agent for Agentic KB Factory.
Coordinates the Collector and Healer agents.
NOTE: google-adk 0.1.0 doesn't have Workflow, so using manual orchestration.
"""

import logging
from typing import Dict, Any

from backend.config import settings
from .collector import CollectorAgent, run_collector_pipeline
from .healer import HealerAgent, run_healing_pipeline

logger = logging.getLogger(__name__)


# Placeholder for future Workflow integration
# OrchestratorAgent would coordinate agents automatically when Workflow is available
OrchestratorAgent = None


async def run_orchestration(collector_id: str) -> Dict[str, Any]:
    """
    Run the complete orchestration pipeline.
    
    This coordinates:
    1. Collector Agent extracts data
    2. If extraction fails, Healer Agent repairs selectors
    3. Collector Agent retries extraction
    """
    logger.info(f"Starting orchestration for collector: {collector_id}")
    
    result = await run_collector_pipeline(collector_id)
    
    return result
