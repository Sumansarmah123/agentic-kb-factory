"""
Gemini AI service for Agentic KB Factory.
Handles content classification, selector healing, and summarization.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from google import genai
from google.genai import types

from backend.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of content classification."""
    category: str
    urgency: str
    executive_summary: str
    breaking_change: bool
    key_entities: list


@dataclass
class SelectorHealingResult:
    """Result of selector healing."""
    new_selector: str
    confidence_score: float
    reasoning: str
    alternative_selectors: list


class GeminiService:
    """
    Service for interacting with Gemini AI.
    
    Key capabilities:
    - Content classification (category, urgency, breaking changes)
    - CSS selector healing (find equivalent selectors)
    - Executive summary generation
    """
    
    _instance: Optional["GeminiService"] = None
    
    def __new__(cls) -> "GeminiService":
        """Singleton pattern for Gemini client."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize Gemini client."""
        if self._initialized:
            return
        
        self._client: Optional[genai.Client] = None
        self._initialized = True
    
    def _get_client(self) -> genai.Client:
        """Get or create Gemini client."""
        if self._client is None:
            if settings.google_genai_use_enterprise:
                # Use Vertex AI
                self._client = genai.Client(
                    vertexai=True,
                    project=settings.gcp_project_id,
                    location=settings.gcp_location,
                )
            else:
                # Use Gemini API
                if not settings.gemini_api_key:
                    raise ValueError("GEMINI_API_KEY is required when not using enterprise mode")
                self._client = genai.Client(api_key=settings.gemini_api_key)
            
            logger.info("Gemini client initialized")
        return self._client
    
    # ============================================
    # Content Classification
    # ============================================
    
    async def classify_content(
        self,
        html_snippet: str,
        context: Optional[str] = None,
    ) -> ClassificationResult:
        """
        Classify HTML content for importance and type.
        
        Args:
            html_snippet: HTML content to classify
            context: Optional context about the source
            
        Returns:
            ClassificationResult with category, urgency, summary, etc.
        """
        client = self._get_client()
        
        prompt = f"""Analyze the following HTML content and classify it.

Context: {context or "Enterprise knowledge base article"}

HTML Content:
```html
{html_snippet[:8000]}
```

Respond in JSON format with these fields:
{{
    "category": "one of: announcement, policy, process, technical, meeting, other",
    "urgency": "one of: critical, high, medium, low",
    "executive_summary": "2-3 sentence summary of the key points",
    "breaking_change": true/false - whether this represents a breaking change or critical update,
    "key_entities": ["list", "of", "key", "people", "products", "dates", "mentioned"]
}}

Only output the JSON, no additional text."""

        try:
            response = client.models.generate_content(
                model=settings.collector_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=1024,
                    response_mime_type="application/json",
                ),
            )
            
            # Parse JSON response
            result = json.loads(response.text)
            
            return ClassificationResult(
                category=result.get("category", "other"),
                urgency=result.get("urgency", "medium"),
                executive_summary=result.get("executive_summary", ""),
                breaking_change=result.get("breaking_change", False),
                key_entities=result.get("key_entities", []),
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse classification response: {e}")
            # Return default classification
            return ClassificationResult(
                category="other",
                urgency="medium",
                executive_summary="Unable to classify content",
                breaking_change=False,
                key_entities=[],
            )
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            raise
    
    # ============================================
    # Selector Healing
    # ============================================
    
    async def heal_selector(
        self,
        broken_html: str,
        old_selector: str,
        field_name: str,
        context: Optional[str] = None,
    ) -> SelectorHealingResult:
        """
        Use Gemini to find an equivalent CSS selector when the old one breaks.
        
        This is the KEY INNOVATION of the Agentic KB Factory.
        
        Args:
            broken_html: Current HTML that the old selector doesn't work on
            old_selector: The CSS selector that is now broken
            field_name: Name of the field being extracted (e.g., "title", "author")
            context: Optional context about what the selector was extracting
            
        Returns:
            SelectorHealingResult with new selector, confidence, and reasoning
        """
        client = self._get_client()
        
        prompt = f"""You are a CSS selector expert. A web scraper's selector has broken because the website's HTML structure changed.

**Field Name:** {field_name}
**Old Selector (broken):** `{old_selector}`
**Context:** {context or f"Extracting {field_name} from the page"}

**Current HTML:**
```html
{broken_html[:10000]}
```

TASK:
1. Analyze the HTML to find where the {field_name} content now appears
2. Create a new CSS selector that will extract the same content
3. Provide a confidence score (0.0-1.0) for your selector
4. Explain your reasoning

Respond in JSON format:
{{
    "new_selector": "the new CSS selector",
    "confidence_score": 0.95,
    "reasoning": "explanation of why this selector works",
    "alternative_selectors": ["backup selector 1", "backup selector 2"]
}}

Guidelines for good selectors:
- Prefer stable attributes like data-*, id, aria-*
- Avoid auto-generated classes like .css-abc123
- Use semantic HTML elements when possible
- Keep selectors as simple as possible

Only output the JSON, no additional text."""

        try:
            response = client.models.generate_content(
                model=settings.healer_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=2048,
                    response_mime_type="application/json",
                ),
            )
            
            result = json.loads(response.text)
            
            return SelectorHealingResult(
                new_selector=result.get("new_selector", ""),
                confidence_score=result.get("confidence_score", 0.0),
                reasoning=result.get("reasoning", ""),
                alternative_selectors=result.get("alternative_selectors", []),
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse healing response: {e}")
            raise ValueError(f"Invalid healing response: {response.text}")
        except Exception as e:
            logger.error(f"Selector healing failed: {e}")
            raise
    
    # ============================================
    # Summary Generation
    # ============================================
    
    async def generate_summary(
        self,
        items: list,
        max_length: int = 500,
    ) -> str:
        """
        Generate an executive summary of extracted items.
        
        Args:
            items: List of extracted items
            max_length: Maximum length of summary
            
        Returns:
            Executive summary string
        """
        if not items:
            return "No items extracted."
        
        client = self._get_client()
        
        # Convert items to text representation
        items_text = json.dumps(items[:20], indent=2)[:6000]  # Limit context
        
        prompt = f"""Create a concise executive summary of the following extracted items.

Items (JSON):
{items_text}

Requirements:
- Summarize in 2-4 sentences
- Highlight the most important updates or changes
- Keep it under {max_length} characters
- Write for a busy executive who needs quick insights

Only output the summary, nothing else."""

        try:
            response = client.models.generate_content(
                model=settings.collector_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    max_output_tokens=max_length,
                ),
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return f"Extracted {len(items)} items. Summary generation failed."
    
    # ============================================
    # DOM Analysis
    # ============================================
    
    async def analyze_dom_changes(
        self,
        old_html: str,
        new_html: str,
        selector: str,
    ) -> Dict[str, Any]:
        """
        Analyze what changed in the DOM between two versions.
        
        Args:
            old_html: Previous HTML version
            new_html: Current HTML version
            selector: The affected selector
            
        Returns:
            Analysis of changes
        """
        client = self._get_client()
        
        prompt = f"""Analyze the DOM changes between two HTML versions.

**Selector that broke:** `{selector}`

**Old HTML (previous working version):**
```html
{old_html[:5000]}
```

**New HTML (current broken version):**
```html
{new_html[:5000]}
```

Identify:
1. What structural changes occurred
2. Why the old selector no longer works
3. What patterns remain stable

Respond in JSON:
{{
    "structural_changes": ["list of changes"],
    "selector_failure_reason": "why it broke",
    "stable_patterns": ["patterns that remain consistent"],
    "recommendation": "suggested approach for future stability"
}}"""

        try:
            response = client.models.generate_content(
                model=settings.healer_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                    response_mime_type="application/json",
                ),
            )
            
            return json.loads(response.text)
            
        except Exception as e:
            logger.error(f"DOM analysis failed: {e}")
            return {
                "structural_changes": [],
                "selector_failure_reason": str(e),
                "stable_patterns": [],
                "recommendation": "Unable to analyze",
            }
    
    # ============================================
    # Health Check
    # ============================================
    
    async def health_check(self) -> bool:
        """
        Check if Gemini service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            client = self._get_client()
            response = client.models.generate_content(
                model=settings.collector_model,
                contents="Say 'ok'",
                config=types.GenerateContentConfig(
                    temperature=0,
                    max_output_tokens=10,
                ),
            )
            return "ok" in response.text.lower()
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return False


# Singleton instance
gemini_service = GeminiService()
