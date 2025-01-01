"""PyAccessibility - Web Accessibility Testing Tool."""

from .rules.base import Rule, RuleViolation
from .scanner import AccessibilityScanner

__version__ = "0.1.0"
__all__ = ["AccessibilityScanner", "Rule", "RuleViolation"]
