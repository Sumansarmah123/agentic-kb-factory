"""
Secured Gemini AI service with Model Armor integration.
Extends the base GeminiService with security guardrails.
"""

import logging
from typing import Optional

from backend.services.gemini import (
    GeminiService,
    ClassificationResult,
    SelectorHealingResult,
)
from backend.services.model_armor import model_armor, SecurityCheckResult

logger = logging.getLogger(__name__)


class SecuredGeminiService(GeminiService):
    """
    Gemini service with integrated Model Armor security.
    
    All inputs are validated before sending to Gemini.
    All outputs are validated before returning to caller.
    """
    
    def _validate_input(self, text: str, field_name: str) -> None:
        """
        Validate input for prompt injection and security risks.
        
        Args:
            text: Input text to validate
            field_name: Name of the field (for error messages)
            
        Raises:
            ValueError: If input fails security validation
        """
        result = model_armor.check_prompt_injection(text)
        
        if not result.is_safe:
            logger.error(
                f"Security check failed for {field_name}: "
                f"risk={result.risk_level}, patterns={result.detected_patterns}"
            )
            raise ValueError(
                f"Input validation failed for {field_name}: "
                f"Detected {result.risk_level} risk patterns. "
                f"Please review your input."
            )
    
    def _validate_selector(self, selector: str) -> None:
        """
        Validate CSS selector for safety.
        
        Args:
            selector: CSS selector to validate
            
        Raises:
            ValueError: If selector fails validation
        """
        result = model_armor.validate_css_selector(selector)
        
        if not result.is_safe:
            logger.error(
                f"Invalid selector: risk={result.risk_level}, "
                f"patterns={result.detected_patterns}"
            )
            raise ValueError(
                f"CSS selector validation failed: {result.detected_patterns}"
            )
    
    def _validate_confidence(self, score: float) -> None:
        """
        Validate confidence score is in valid range.
        
        Args:
            score: Confidence score to validate
            
        Raises:
            ValueError: If score is invalid
        """
        result = model_armor.validate_confidence_score(score, 0.0, 1.0)
        
        if not result.is_safe:
            raise ValueError(
                f"Invalid confidence score: {score}. Must be between 0.0 and 1.0"
            )
    
    # ============================================
    # Secured Content Classification
    # ============================================
    
    async def classify_content(
        self,
        html_snippet: str,
        context: Optional[str] = None,
    ) -> ClassificationResult:
        """
        Classify content with input validation.
        
        Args:
            html_snippet: HTML to classify
            context: Optional context
            
        Returns:
            ClassificationResult
            
        Raises:
            ValueError: If inputs fail security validation
        """
        # Sanitize HTML input
        html_snippet = model_armor.sanitize_html_input(html_snippet)
        
        # Validate context if provided
        if context:
            self._validate_input(context, "context")
        
        # Call parent implementation
        return await super().classify_content(html_snippet, context)
    
    # ============================================
    # Secured Selector Healing
    # ============================================
    
    async def heal_selector(
        self,
        broken_html: str,
        old_selector: str,
        field_name: str,
        context: Optional[str] = None,
    ) -> SelectorHealingResult:
        """
        Heal selector with comprehensive security validation.
        
        This is the CRITICAL SECURITY CHECKPOINT for the self-healing system.
        
        Args:
            broken_html: Current HTML
            old_selector: Broken selector
            field_name: Field being extracted
            context: Optional context
            
        Returns:
            SelectorHealingResult with validated output
            
        Raises:
            ValueError: If any input or output fails security validation
        """
        # Validate inputs
        self._validate_input(field_name, "field_name")
        self._validate_selector(old_selector)
        
        if context:
            self._validate_input(context, "context")
        
        # Sanitize HTML
        broken_html = model_armor.sanitize_html_input(broken_html)
        
        # Call parent implementation
        result = await super().heal_selector(
            broken_html=broken_html,
            old_selector=old_selector,
            field_name=field_name,
            context=context,
        )
        
        # Validate output
        self._validate_selector(result.new_selector)
        self._validate_confidence(result.confidence_score)
        
        # Validate alternative selectors
        for alt_selector in result.alternative_selectors:
            self._validate_selector(alt_selector)
        
        logger.info(
            f"Selector healing validated: field={field_name}, "
            f"confidence={result.confidence_score:.2f}"
        )
        
        return result
    
    # ============================================
    # Secured Summary Generation
    # ============================================
    
    async def generate_summary(
        self,
        items: list,
        max_length: int = 500,
    ) -> str:
        """
        Generate summary with output validation.
        
        Args:
            items: Items to summarize
            max_length: Max summary length
            
        Returns:
            Validated summary string
        """
        # Call parent implementation
        summary = await super().generate_summary(items, max_length)
        
        # Validate output for dangerous content
        result = model_armor.validate_llm_output(summary, "text")
        if not result.is_safe:
            logger.warning(
                f"Summary validation warning: {result.detected_patterns}"
            )
            return "Summary generation completed but output validation flagged potential issues."
        
        return summary


# Singleton instance (secured version)
secured_gemini_service = SecuredGeminiService()
