"""
Model Armor: Security guardrails for LLM interactions.
Prevents prompt injection, output manipulation, and PII leakage.
"""

import re
import logging
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SecurityCheckResult:
    """Result of security validation."""
    is_safe: bool
    risk_level: str  # "safe", "low", "medium", "high", "critical"
    detected_patterns: list[str]
    sanitized_text: Optional[str] = None


class ModelArmorService:
    """
    Security service for LLM interactions.
    
    Implements:
    1. Prompt injection detection
    2. Output validation
    3. PII detection and redaction
    4. Content filtering
    """
    
    # Prompt injection patterns (case-insensitive)
    INJECTION_PATTERNS = [
        # Direct instruction override
        r"ignore\s+(previous|all|above|prior)\s+(instructions?|prompts?|rules?)",
        r"disregard\s+(previous|all|above|prior)",
        r"forget\s+(previous|all|above|everything)",
        
        # System manipulation
        r"system\s+(override|mode|prompt|instruction)",
        r"developer\s+mode",
        r"admin\s+mode",
        r"sudo\s+mode",
        r"root\s+access",
        r"bypass\s+(security|safety|filter|check)",
        
        # Role manipulation
        r"(act|behave|pretend|roleplay)\s+as\s+if",
        r"you\s+are\s+now\s+(a|an)\s+",
        r"new\s+instructions?",
        
        # Jailbreak attempts
        r"DAN\s+mode",
        r"jailbreak",
        r"unrestricted\s+mode",
        
        # Direct access attempts
        r"direct\s+access\s+to",
        r"show\s+me\s+your\s+(instructions?|system\s+prompt)",
        
        # Encoding tricks
        r"base64",
        r"rot13",
        r"hex\s+encode",
    ]
    
    # CSS selector safety patterns
    SAFE_SELECTOR_PATTERN = r'^[a-zA-Z0-9\s\.\#\[\]\=\"\'\:\-\>\~\+\*\,\(\)]+$'
    
    # Dangerous HTML/JS patterns
    DANGEROUS_HTML_PATTERNS = [
        r"<script",
        r"javascript:",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onload\s*=",
        r"eval\s*\(",
        r"<iframe",
    ]
    
    # PII patterns (for detection, not automatic redaction)
    PII_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    }
    
    def __init__(self):
        """Initialize Model Armor service."""
        self._compiled_injection_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.INJECTION_PATTERNS
        ]
        self._compiled_html_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_HTML_PATTERNS
        ]
    
    # ============================================
    # Prompt Injection Detection
    # ============================================
    
    def check_prompt_injection(self, text: str) -> SecurityCheckResult:
        """
        Check for prompt injection attempts.
        
        Args:
            text: User input to validate
            
        Returns:
            SecurityCheckResult with detection results
        """
        if not text:
            return SecurityCheckResult(
                is_safe=True,
                risk_level="safe",
                detected_patterns=[],
            )
        
        detected = []
        text_lower = text.lower()
        
        # Check each injection pattern
        for pattern in self._compiled_injection_patterns:
            match = pattern.search(text_lower)
            if match:
                detected.append(match.group(0))
        
        if detected:
            risk_level = "critical" if len(detected) > 2 else "high"
            logger.warning(f"Prompt injection detected: {detected}")
            return SecurityCheckResult(
                is_safe=False,
                risk_level=risk_level,
                detected_patterns=detected,
            )
        
        return SecurityCheckResult(
            is_safe=True,
            risk_level="safe",
            detected_patterns=[],
        )
    
    # ============================================
    # CSS Selector Validation
    # ============================================
    
    def validate_css_selector(self, selector: str) -> SecurityCheckResult:
        """
        Validate a CSS selector for safety.
        
        Args:
            selector: CSS selector to validate
            
        Returns:
            SecurityCheckResult with validation result
        """
        if not selector:
            return SecurityCheckResult(
                is_safe=False,
                risk_level="high",
                detected_patterns=["empty selector"],
            )
        
        # Check for valid CSS syntax
        if not re.match(self.SAFE_SELECTOR_PATTERN, selector):
            return SecurityCheckResult(
                is_safe=False,
                risk_level="high",
                detected_patterns=["invalid CSS characters"],
            )
        
        # Check for overly permissive selectors (security risk)
        dangerous_selectors = ["*", "body", "html", "body *", "html *"]
        if selector.strip() in dangerous_selectors:
            return SecurityCheckResult(
                is_safe=False,
                risk_level="medium",
                detected_patterns=["overly permissive selector"],
            )
        
        # Check for executable content
        for pattern in self._compiled_html_patterns:
            if pattern.search(selector):
                return SecurityCheckResult(
                    is_safe=False,
                    risk_level="critical",
                    detected_patterns=["potentially executable content"],
                )
        
        return SecurityCheckResult(
            is_safe=True,
            risk_level="safe",
            detected_patterns=[],
        )
    
    # ============================================
    # Output Validation
    # ============================================
    
    def validate_llm_output(
        self,
        output: str,
        expected_format: str = "json",
    ) -> SecurityCheckResult:
        """
        Validate LLM output for safety and format compliance.
        
        Args:
            output: LLM-generated text
            expected_format: Expected format ("json", "text", "selector")
            
        Returns:
            SecurityCheckResult with validation result
        """
        if not output:
            return SecurityCheckResult(
                is_safe=False,
                risk_level="medium",
                detected_patterns=["empty output"],
            )
        
        # Check for executable content in output
        detected = []
        for pattern in self._compiled_html_patterns:
            match = pattern.search(output)
            if match:
                detected.append(match.group(0))
        
        if detected:
            return SecurityCheckResult(
                is_safe=False,
                risk_level="high",
                detected_patterns=detected,
            )
        
        # Format-specific validation
        if expected_format == "selector":
            return self.validate_css_selector(output)
        
        return SecurityCheckResult(
            is_safe=True,
            risk_level="safe",
            detected_patterns=[],
        )
    
    # ============================================
    # PII Detection
    # ============================================
    
    def detect_pii(self, text: str) -> Tuple[bool, dict]:
        """
        Detect personally identifiable information in text.
        
        Args:
            text: Text to scan for PII
            
        Returns:
            Tuple of (has_pii: bool, findings: dict)
        """
        findings = {}
        
        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                findings[pii_type] = len(matches)
        
        has_pii = len(findings) > 0
        
        if has_pii:
            logger.warning(f"PII detected: {findings}")
        
        return has_pii, findings
    
    # ============================================
    # Input Sanitization
    # ============================================
    
    def sanitize_html_input(self, html: str, max_length: int = 50000) -> str:
        """
        Sanitize HTML input before sending to LLM.
        
        Args:
            html: Raw HTML input
            max_length: Maximum allowed length
            
        Returns:
            Sanitized HTML
        """
        # Truncate to max length
        sanitized = html[:max_length]
        
        # Remove inline scripts (safety measure)
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove event handlers
        sanitized = re.sub(r'\s*on\w+\s*=\s*["\'].*?["\']', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    # ============================================
    # Confidence Score Validation
    # ============================================
    
    def validate_confidence_score(
        self,
        score: float,
        min_threshold: float = 0.0,
        max_threshold: float = 1.0,
    ) -> SecurityCheckResult:
        """
        Validate confidence score from LLM is in valid range.
        
        Args:
            score: Confidence score from LLM
            min_threshold: Minimum valid value
            max_threshold: Maximum valid value
            
        Returns:
            SecurityCheckResult with validation result
        """
        if not isinstance(score, (int, float)):
            return SecurityCheckResult(
                is_safe=False,
                risk_level="high",
                detected_patterns=["invalid score type"],
            )
        
        if score < min_threshold or score > max_threshold:
            return SecurityCheckResult(
                is_safe=False,
                risk_level="medium",
                detected_patterns=["score out of range"],
            )
        
        return SecurityCheckResult(
            is_safe=True,
            risk_level="safe",
            detected_patterns=[],
        )
    
    # ============================================
    # Comprehensive Check
    # ============================================
    
    def comprehensive_check(
        self,
        user_input: Optional[str] = None,
        llm_output: Optional[str] = None,
        selector: Optional[str] = None,
        html: Optional[str] = None,
    ) -> SecurityCheckResult:
        """
        Run comprehensive security checks on all inputs/outputs.
        
        Args:
            user_input: User-provided text
            llm_output: LLM-generated text
            selector: CSS selector
            html: HTML content
            
        Returns:
            Aggregated SecurityCheckResult
        """
        all_detected = []
        highest_risk = "safe"
        
        # Check user input for prompt injection
        if user_input:
            result = self.check_prompt_injection(user_input)
            if not result.is_safe:
                all_detected.extend(result.detected_patterns)
                highest_risk = self._max_risk(highest_risk, result.risk_level)
        
        # Validate LLM output
        if llm_output:
            result = self.validate_llm_output(llm_output)
            if not result.is_safe:
                all_detected.extend(result.detected_patterns)
                highest_risk = self._max_risk(highest_risk, result.risk_level)
        
        # Validate CSS selector
        if selector:
            result = self.validate_css_selector(selector)
            if not result.is_safe:
                all_detected.extend(result.detected_patterns)
                highest_risk = self._max_risk(highest_risk, result.risk_level)
        
        # Sanitize HTML (just warn, don't block)
        if html:
            has_pii, findings = self.detect_pii(html)
            if has_pii:
                all_detected.append(f"PII detected: {findings}")
                highest_risk = self._max_risk(highest_risk, "low")
        
        is_safe = highest_risk in ["safe", "low"]
        
        return SecurityCheckResult(
            is_safe=is_safe,
            risk_level=highest_risk,
            detected_patterns=all_detected,
        )
    
    def _max_risk(self, risk1: str, risk2: str) -> str:
        """Return the higher risk level."""
        risk_order = ["safe", "low", "medium", "high", "critical"]
        idx1 = risk_order.index(risk1) if risk1 in risk_order else 0
        idx2 = risk_order.index(risk2) if risk2 in risk_order else 0
        return risk_order[max(idx1, idx2)]


# Singleton instance
model_armor = ModelArmorService()
