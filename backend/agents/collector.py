"""
Collector Agent for Agentic KB Factory.
Responsible for fetching and extracting content from knowledge bases.
NOW WITH: Pub/Sub healing trigger + OpenTelemetry tracing
"""

import time
import uuid
import logging
from typing import Dict, Any

import httpx
from bs4 import BeautifulSoup

from google.adk import Agent
from google.adk.tools import FunctionTool

from backend.config import settings
from backend.services.firestore import firestore_service
from backend.services.pubsub import pubsub_service
from backend.observability import ObservabilityService
from backend.models.schemas import (
    ExtractionLogCreate,
    ExtractionStatus,
)

logger = logging.getLogger(__name__)


def fetch_url(url: str) -> str:
    """Fetch HTML content from a URL."""
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text


def extract_items(html: str, selectors: Dict[str, str]) -> Dict[str, Any]:
    """Extract items from HTML using CSS selectors."""
    soup = BeautifulSoup(html, "lxml")
    extracted = {}
    extraction_log = []
    
    for field_name, selector in selectors.items():
        try:
            elements = soup.select(selector)
            if elements:
                if len(elements) == 1:
                    extracted[field_name] = elements[0].get_text(strip=True)
                else:
                    extracted[field_name] = [el.get_text(strip=True) for el in elements]
                extraction_log.append({
                    "field": field_name,
                    "selector": selector,
                    "found": len(elements),
                    "status": "success",
                })
            else:
                extracted[field_name] = None
                extraction_log.append({
                    "field": field_name,
                    "selector": selector,
                    "found": 0,
                    "status": "empty",
                })
        except Exception as e:
            extracted[field_name] = None
            extraction_log.append({
                "field": field_name,
                "selector": selector,
                "found": 0,
                "status": "error",
                "error": str(e),
            })
    
    return {
        "extracted": extracted,
        "log": extraction_log,
        "total_fields": len(selectors),
        "successful_fields": sum(1 for l in extraction_log if l["status"] == "success"),
    }


# Create ADK Agent (using google-adk 0.1.0 API)
CollectorAgent = Agent(
    name="collector_agent",
    model=settings.collector_model,
    instruction="Extract structured data from web pages using CSS selectors.",
    tools=[
        FunctionTool(fetch_url),
        FunctionTool(extract_items),
    ],
)


async def run_collector_pipeline(collector_id: str) -> Dict[str, Any]:
    """
    Run the complete collector pipeline.
    NOW WITH: Pub/Sub healing trigger when extraction fails.
    """
    start_time = time.time()
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    log_id = f"log-{uuid.uuid4().hex[:12]}"
    
    collector = await firestore_service.get_collector(collector_id)
    if not collector:
        return {"success": False, "error": f"Collector {collector_id} not found"}
    
    try:
        html = fetch_url(collector.target_url)
        extraction = extract_items(html, collector.css_selectors)
        
        items_extracted = extraction["successful_fields"]
        status = ExtractionStatus.SUCCESS if items_extracted > 0 else ExtractionStatus.BROKEN_DOM
        
        # 🔥 NEW: Trace agent decision
        ObservabilityService.trace_agent_decision(
            agent_name="collector",
            decision=f"extracted_{items_extracted}_fields",
            reasoning=f"Successfully extracted {items_extracted}/{extraction['total_fields']} fields",
            confidence=items_extracted / extraction['total_fields'] if extraction['total_fields'] > 0 else 0.0,
        )
        
        # 🔥 NEW: Trigger healing via Pub/Sub if extraction failed
        if items_extracted == 0 and extraction['total_fields'] > 0:
            logger.warning(f"Extraction failed for {collector_id}, triggering healing")
            
            # Find first failed field
            failed_field = next(
                (log for log in extraction["log"] if log["status"] in ["empty", "error"]),
                None
            )
            
            if failed_field:
                await pubsub_service.publish_healing_event({
                    "collector_id": collector_id,
                    "field_name": failed_field["field"],
                    "old_selector": failed_field["selector"],
                    "job_id": job_id,
                })
                logger.info(f"Published healing event for {failed_field['field']}")
        
        log_data = ExtractionLogCreate(
            collector_id=collector_id,
            status=status,
            items_extracted=items_extracted,
            raw_payload=[extraction["extracted"]],
            summary=f"Extracted {items_extracted} fields",
        )
        
        await firestore_service.log_extraction(log_id, log_data)
        await firestore_service.update_collector_status(
            collector_id,
            "active",
            increment_success=(status == ExtractionStatus.SUCCESS),
        )
        
        duration_ms = (time.time() - start_time) * 1000
        ObservabilityService.trace_extraction(
            collector_id=collector_id,
            field_count=extraction['total_fields'],
            items_extracted=items_extracted,
            duration_ms=duration_ms,
            success=(status == ExtractionStatus.SUCCESS),
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "items_extracted": items_extracted,
            "status": status,
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return {"success": False, "error": str(e)}
