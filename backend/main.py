"""
FastAPI Backend for Agentic KB Factory.
Production-ready REST API for the knowledge base collection system.
"""

import uuid
import logging
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.services.firestore import firestore_service
from backend.services.gemini_secured import secured_gemini_service
from backend.services.pubsub import pubsub_service
from backend.observability import ObservabilityService
from backend.models.schemas import (
    CollectorCreate,
    CollectorUpdate,
    CollectorConfig,
    CollectorListResponse,
    HealthCheckResponse,
    HealthStatus,
    TriggerRunResponse,
    ExtractionLogListResponse,
    HealingLogListResponse,
    ExportDataResponse,
)
from backend.agents.collector import run_collector_pipeline

logger = logging.getLogger(__name__)


# ============================================
# Lifecycle Management
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting Agentic KB Factory...")
    
    # Initialize OpenTelemetry observability with Cloud Trace
    if settings.gcp_project_id:
        try:
            ObservabilityService.initialize(
                service_name=settings.app_name,
                project_id=settings.gcp_project_id,
            )
            logger.info("Observability initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize observability: {e}")
    
    yield
    logger.info("Shutting down...")
    await firestore_service.close()


# ============================================
# FastAPI Application
# ============================================

app = FastAPI(
    title="Agentic KB Factory API",
    description="Autonomous Enterprise Knowledge Base Collector with Self-Healing DOM Engine",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting Configuration
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================
# Health & Status Endpoints
# ============================================

@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint.
    Verifies connectivity to all required services.
    """
    with ObservabilityService.trace_operation("health_check"):
        try:
            # Check Firestore
            firestore_ok = True
            try:
                await firestore_service.get_statistics()
            except Exception as e:
                logger.warning(f"Firestore health check failed: {e}")
                firestore_ok = False
            
            # Check Gemini
            gemini_ok = await secured_gemini_service.health_check()
            
            # Determine overall status
            if firestore_ok and gemini_ok:
                status = HealthStatus.HEALTHY
            else:
                status = HealthStatus.DEGRADED
            
            return HealthCheckResponse(
                status=status,
                app_name=settings.app_name,
                version=settings.app_version,
                gcp_connected=True,
                firestore_connected=firestore_ok,
                gemini_connected=gemini_ok,
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthCheckResponse(
                status=HealthStatus.UNHEALTHY,
                app_name=settings.app_name,
                version=settings.app_version,
                gcp_connected=False,
                firestore_connected=False,
                gemini_connected=False,
            )


# ============================================
# Collector Endpoints
# ============================================

@app.get("/api/collectors", response_model=CollectorListResponse)
async def list_collectors(active_only: bool = Query(False)):
    """List all collectors."""
    try:
        collectors = await firestore_service.list_collectors(
            active_only=active_only,
            limit=100,
        )
        active_count = sum(1 for c in collectors if c.is_active)
        unhealthy_count = sum(1 for c in collectors if c.status == "error")
        
        return CollectorListResponse(
            collectors=collectors,
            total=len(collectors),
            active=active_count,
            unhealthy=unhealthy_count,
        )
    except Exception as e:
        logger.error(f"Failed to list collectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/collectors", response_model=CollectorConfig)
@limiter.limit("10/minute")
async def create_collector(request: Request, data: CollectorCreate):
    """Create a new collector."""
    with ObservabilityService.trace_operation("create_collector", {"target_url": data.target_url}):
        try:
            collector_id = f"collector-{uuid.uuid4().hex[:12]}"
            collector = await firestore_service.create_collector(collector_id, data)
            return collector
        except Exception as e:
            logger.error(f"Failed to create collector: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/collectors/{collector_id}", response_model=CollectorConfig)
async def get_collector(collector_id: str):
    """Get a specific collector."""
    try:
        collector = await firestore_service.get_collector(collector_id)
        if not collector:
            raise HTTPException(status_code=404, detail="Collector not found")
        return collector
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collector: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/collectors/{collector_id}", response_model=CollectorConfig)
async def update_collector(collector_id: str, data: CollectorUpdate):
    """Update a collector."""
    try:
        collector = await firestore_service.update_collector(collector_id, data)
        if not collector:
            raise HTTPException(status_code=404, detail="Collector not found")
        return collector
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update collector: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/collectors/{collector_id}")
async def delete_collector(collector_id: str):
    """Delete a collector."""
    try:
        deleted = await firestore_service.delete_collector(collector_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Collector not found")
        return {"message": "Collector deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete collector: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Job Execution Endpoints
# ============================================

@app.post("/api/collectors/{collector_id}/run", response_model=TriggerRunResponse)
@limiter.limit("10/minute")
async def trigger_collector_run(request: Request, collector_id: str, background_tasks: BackgroundTasks):
    """Trigger an on-demand extraction run."""
    with ObservabilityService.trace_operation("trigger_run", {"collector_id": collector_id}):
        try:
            job_id = f"job-{uuid.uuid4().hex[:12]}"
            
            # Run in background
            background_tasks.add_task(run_collector_pipeline, collector_id)
            
            return TriggerRunResponse(
                job_id=job_id,
                collector_id=collector_id,
                status="queued",
                message="Extraction job queued for execution",
            )
        except Exception as e:
            logger.error(f"Failed to trigger run: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Logs & History Endpoints
# ============================================

@app.get("/api/extraction-logs", response_model=ExtractionLogListResponse)
async def list_extraction_logs(
    collector_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
):
    """List extraction logs."""
    try:
        logs = await firestore_service.list_extraction_logs(
            collector_id=collector_id,
            limit=limit,
        )
        return ExtractionLogListResponse(logs=logs, total=len(logs))
    except Exception as e:
        logger.error(f"Failed to list extraction logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/healing-logs", response_model=HealingLogListResponse)
async def list_healing_logs(
    collector_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
):
    """List self-healing events."""
    try:
        events = await firestore_service.list_healing_events(
            collector_id=collector_id,
            limit=limit,
        )
        successful = sum(1 for e in events if e.status == "success")
        failed = sum(1 for e in events if e.status == "failed")
        
        return HealingLogListResponse(
            events=events,
            total=len(events),
            successful=successful,
            failed=failed,
        )
    except Exception as e:
        logger.error(f"Failed to list healing logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Export Endpoint
# ============================================

@app.get("/api/export/json", response_model=ExportDataResponse)
async def export_data():
    """Export all data as JSON."""
    try:
        collectors = await firestore_service.list_collectors(limit=1000)
        logs = await firestore_service.list_extraction_logs(limit=1000)
        events = await firestore_service.list_healing_events(limit=1000)
        
        return ExportDataResponse(
            collectors=collectors,
            extraction_logs=logs,
            healing_events=events,
        )
    except Exception as e:
        logger.error(f"Failed to export data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Architecture Endpoint
# ============================================

@app.get("/api/architecture")
async def get_architecture():
    """Get architecture diagram data."""
    return {
        "system": "Agentic KB Factory",
        "components": [
            {
                "name": "Collector Agent",
                "type": "ADK Agent",
                "responsibility": "Fetch and extract web content",
            },
            {
                "name": "Healer Agent",
                "type": "ADK Agent",
                "responsibility": "Repair broken CSS selectors",
            },
            {
                "name": "Gemini 3.5",
                "type": "LLM",
                "responsibility": "Content classification and selector healing",
            },
            {
                "name": "Firestore",
                "type": "Database",
                "responsibility": "Persistent state and audit logs",
            },
            {
                "name": "Pub/Sub",
                "type": "Event Bus",
                "responsibility": "Async job dispatching",
            },
        ],
        "track": "Fortified Enterprise Fleet",
        "features": [
            "Autonomous Self-Healing DOM Engine",
            "Multi-agent orchestration with ADK 2.0",
            "Enterprise-grade state management",
            "Production-ready error handling",
        ],
    }


# ============================================
# Root Endpoint
# ============================================

@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "name": "Agentic KB Factory",
        "description": "Autonomous Enterprise Knowledge Base Collector with Self-Healing DOM Engine",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


# ============================================
# Static File Serving (Production)
# ============================================

# Serve frontend build (production only)
frontend_dist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist_path):
    # Serve static assets
    assets_path = os.path.join(frontend_dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    
    # Serve index.html for all non-API routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve React frontend for non-API routes."""
        # Skip API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Serve index.html for all other routes (SPA)
        index_path = os.path.join(frontend_dist_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend not built")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)


# ============================================
# Agent Registry Endpoints (Enterprise Fleet Requirement)
# ============================================

from backend.services.agent_registry import agent_registry_service

@app.get("/api/registry/agents")
async def list_registered_agents(
    department: Optional[str] = Query(None),
    approved_only: bool = Query(True),
):
    """
    List all registered agents in the enterprise catalog.
    
    Track Requirement: Agent Registry for discovery and governance.
    """
    with ObservabilityService.trace_operation("list_agents", {"department": department}):
        try:
            agents = await agent_registry_service.discover_agents(
                department=department,
                approved_only=approved_only,
            )
            return {"agents": agents, "count": len(agents)}
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/registry/stats")
async def get_registry_stats():
    """Get agent registry statistics."""
    with ObservabilityService.trace_operation("registry_stats"):
        try:
            stats = await agent_registry_service.get_agent_stats()
            return stats
        except Exception as e:
            logger.error(f"Failed to get registry stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))
