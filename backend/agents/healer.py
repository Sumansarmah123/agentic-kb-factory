"""
Self-Healing Agent for Agentic KB Factory.
Autonomously repairs broken CSS selectors using Gemini AI.
NOW WITH: OpenTelemetry tracing for agent decisions
"""

import uuid
import logging
from typing import Dict, Any

import httpx
from bs4 import BeautifulSoup

from google.adk import Agent
from google.adk.tools import FunctionTool

from backend.config import settings
from backend.services.firestore import firestore_service
from backend.services.gemini import gemini_service
from backend.observability import ObservabilityService
from backend.models.schemas import SelfHealingEventCreate, HealingStatus

logger = logging.getLogger(__name__)


def fetch_current_html(url: str) -> str:
    """Fetch current HTML from URL."""
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text


# Create ADK Agent
HealerAgent = Agent(
    name="healer_agent",
    model=settings.healer_model,
    instruction="Fix broken CSS selectors by analyzing the current DOM and suggesting new selectors.",
    tools=[
        FunctionTool(fetch_current_html),
    ],
)


async def run_healing_pipeline(
    collector_id: str,
    field_name: str,
    old_selector: str,
) -> Dict[str, Any]:
    """
    Run the healing pipeline for a broken selector.
    NOW WITH: OpenTelemetry tracing for healing decisions.
    """
    event_id = f"heal-{uuid.uuid4().hex[:12]}"
    
    collector = await firestore_service.get_collector(collector_id)
    if not collector:
        return {"success": False, "error": f"Collector {collector_id} not found"}
    
    try:
        # Fetch current HTML
        logger.info(f"Fetching HTML for healing: {collector.target_url}")
        html = fetch_current_html(collector.target_url)
        
        # Use Gemini to heal the selector
        logger.info(f"Healing selector: {old_selector}")
        healing_result = await gemini_service.heal_selector(
            html,
            old_selector,
            field_name,
            context=f"Extracting {field_name} from {collector.source_name}",
        )
        
        # 🔥 NEW: Trace agent decision with reasoning
        ObservabilityService.trace_agent_decision(
            agent_name="healer",
            decision=f"new_selector={healing_result.new_selector}",
            reasoning=healing_result.reasoning,
            confidence=healing_result.confidence_score,
        )
        
        # Check confidence
        if healing_result.confidence_score >= settings.healing_confidence_threshold:
            # Update collector with new selector
            collector.css_selectors[field_name] = healing_result.new_selector
            await firestore_service.update_collector(
                collector_id,
                type('obj', (), {'css_selectors': collector.css_selectors, 'model_dump': lambda *args, **kwargs: {'css_selectors': collector.css_selectors}})(),
            )
            
            status = HealingStatus.SUCCESS
            logger.info(f"✅ Healed {field_name}: {old_selector} → {healing_result.new_selector}")
        else:
            status = HealingStatus.PENDING
            logger.warning(f"⚠️ Low confidence ({healing_result.confidence_score:.2f}) for {field_name}")
        
        # Log healing event
        event_data = SelfHealingEventCreate(
            collector_id=collector_id,
            field_name=field_name,
            old_selector=old_selector,
            new_selector=healing_result.new_selector,
            confidence_score=healing_result.confidence_score,
            status=status,
            reasoning=healing_result.reasoning,
        )
        
        await firestore_service.log_healing_event(event_id, event_data)
        
        # 🔥 NEW: Trace healing operation
        ObservabilityService.trace_healing(
            collector_id=collector_id,
            field_name=field_name,
            old_selector=old_selector,
            new_selector=healing_result.new_selector,
            confidence_score=healing_result.confidence_score,
            success=(status == HealingStatus.SUCCESS),
        )
        
        return {
            "success": True,
            "event_id": event_id,
            "new_selector": healing_result.new_selector,
            "confidence_score": healing_result.confidence_score,
            "status": status,
        }
        
    except Exception as e:
        logger.error(f"Healing failed: {e}")
        
        # Log failed healing event
        event_data = SelfHealingEventCreate(
            collector_id=collector_id,
            field_name=field_name,
            old_selector=old_selector,
            new_selector="",
            confidence_score=0.0,
            status=HealingStatus.FAILED,
            reasoning=f"Healing failed: {str(e)}",
        )
        
        await firestore_service.log_healing_event(event_id, event_data)
        
        return {
            "success": False,
            "event_id": event_id,
            "error": str(e),
        }
