"""
OpenTelemetry observability for Agentic KB Factory.
Provides audit logs and reasoning chain traces for Enterprise Fleet compliance.
"""

import logging
from typing import Optional
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)


class ObservabilityService:
    """
    Centralized observability service for the application.
    
    Features:
    - Distributed tracing with Cloud Trace
    - Audit logging for compliance
    - Reasoning chain tracking for agent decisions
    """
    
    _tracer: Optional[trace.Tracer] = None
    _initialized: bool = False
    
    @classmethod
    def initialize(
        cls,
        service_name: str = "agentic-kb-factory",
        project_id: Optional[str] = None,
    ) -> None:
        """
        Initialize OpenTelemetry with Google Cloud Trace.
        
        Args:
            service_name: Name of the service
            project_id: GCP project ID (required for Cloud Trace)
        """
        if cls._initialized:
            logger.info("Observability already initialized")
            return
        
        # Create resource with service info
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
        })
        
        # Set up tracer provider
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        
        # Add Cloud Trace exporter if project_id provided
        if project_id:
            try:
                cloud_trace_exporter = CloudTraceSpanExporter(project_id=project_id)
                span_processor = BatchSpanProcessor(cloud_trace_exporter)
                tracer_provider.add_span_processor(span_processor)
                logger.info(f"Cloud Trace exporter initialized for project: {project_id}")
            except Exception as e:
                logger.warning(f"Failed to initialize Cloud Trace exporter: {e}")
                logger.info("Continuing without Cloud Trace export")
        else:
            logger.info("No project_id provided; traces will not be exported to Cloud Trace")
        
        cls._tracer = trace.get_tracer(__name__)
        cls._initialized = True
        logger.info("OpenTelemetry observability initialized")
    
    @classmethod
    def get_tracer(cls) -> trace.Tracer:
        """Get the global tracer instance."""
        if not cls._initialized:
            # Initialize with defaults if not already done
            cls.initialize()
        return cls._tracer
    
    @classmethod
    @contextmanager
    def trace_operation(
        cls,
        operation_name: str,
        attributes: Optional[dict] = None,
    ):
        """
        Context manager for tracing an operation.
        
        Usage:
            with ObservabilityService.trace_operation("extract_content", {"collector_id": "123"}):
                result = await extract()
        
        Args:
            operation_name: Name of the operation
            attributes: Optional attributes to attach to the span
        """
        tracer = cls.get_tracer()
        
        with tracer.start_as_current_span(operation_name) as span:
            # Set attributes
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
            
            try:
                yield span
            except Exception as e:
                # Record exception
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    @classmethod
    def trace_extraction(
        cls,
        collector_id: str,
        field_count: int,
        items_extracted: int,
        duration_ms: float,
        success: bool,
    ) -> None:
        """
        Trace an extraction operation.
        
        Args:
            collector_id: ID of the collector
            field_count: Number of fields configured
            items_extracted: Number of items extracted
            duration_ms: Duration in milliseconds
            success: Whether extraction succeeded
        """
        tracer = cls.get_tracer()
        
        with tracer.start_as_current_span("extraction") as span:
            span.set_attribute("collector_id", collector_id)
            span.set_attribute("field_count", field_count)
            span.set_attribute("items_extracted", items_extracted)
            span.set_attribute("duration_ms", duration_ms)
            span.set_attribute("success", success)
            
            if success:
                span.set_status(Status(StatusCode.OK))
            else:
                span.set_status(Status(StatusCode.ERROR, "Extraction failed"))
    
    @classmethod
    def trace_healing(
        cls,
        collector_id: str,
        field_name: str,
        old_selector: str,
        new_selector: str,
        confidence_score: float,
        success: bool,
    ) -> None:
        """
        Trace a selector healing operation.
        
        Args:
            collector_id: ID of the collector
            field_name: Name of the field
            old_selector: Previous selector
            new_selector: New selector
            confidence_score: Confidence in the new selector
            success: Whether healing succeeded
        """
        tracer = cls.get_tracer()
        
        with tracer.start_as_current_span("selector_healing") as span:
            span.set_attribute("collector_id", collector_id)
            span.set_attribute("field_name", field_name)
            span.set_attribute("old_selector", old_selector)
            span.set_attribute("new_selector", new_selector)
            span.set_attribute("confidence_score", confidence_score)
            span.set_attribute("success", success)
            
            # This is a CRITICAL operation for the system
            span.set_attribute("operation_type", "autonomous_healing")
            span.set_attribute("requires_audit", True)
            
            if success:
                span.set_status(Status(StatusCode.OK))
            else:
                span.set_status(Status(StatusCode.ERROR, "Healing failed"))
    
    @classmethod
    def trace_gemini_call(
        cls,
        operation: str,
        model: str,
        prompt_length: int,
        response_length: int,
        latency_ms: float,
    ) -> None:
        """
        Trace a Gemini API call.
        
        Args:
            operation: Operation type (e.g., "heal_selector", "classify")
            model: Gemini model used
            prompt_length: Length of prompt in characters
            response_length: Length of response
            latency_ms: API call latency
        """
        tracer = cls.get_tracer()
        
        with tracer.start_as_current_span("gemini_api_call") as span:
            span.set_attribute("operation", operation)
            span.set_attribute("model", model)
            span.set_attribute("prompt_length", prompt_length)
            span.set_attribute("response_length", response_length)
            span.set_attribute("latency_ms", latency_ms)
            span.set_attribute("ai_provider", "google_gemini")
    
    @classmethod
    def trace_agent_decision(
        cls,
        agent_name: str,
        decision: str,
        reasoning: str,
        confidence: float,
    ) -> None:
        """
        Trace an agent's decision with reasoning chain.
        
        This is CRITICAL for Enterprise Fleet compliance —
        all autonomous decisions must be auditable.
        
        Args:
            agent_name: Name of the agent (e.g., "collector", "healer")
            decision: The decision made
            reasoning: Reasoning behind the decision
            confidence: Confidence in the decision
        """
        tracer = cls.get_tracer()
        
        with tracer.start_as_current_span("agent_decision") as span:
            span.set_attribute("agent_name", agent_name)
            span.set_attribute("decision", decision)
            span.set_attribute("reasoning", reasoning[:500])  # Truncate for storage
            span.set_attribute("confidence", confidence)
            span.set_attribute("autonomous", True)
            span.set_attribute("requires_audit", True)


# Convenience decorator for tracing functions
def traced(operation_name: str):
    """
    Decorator for automatically tracing a function.
    
    Usage:
        @traced("my_operation")
        async def my_function():
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with ObservabilityService.trace_operation(operation_name):
                return await func(*args, **kwargs)
        return wrapper
    return decorator
