from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import time
import httpx
from bs4 import BeautifulSoup
from .rules.base import Rule, RuleViolation


class Severity(Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ScanResult:
    """Container for scan results including violations and metadata."""
    url: Optional[str]
    violations: List[RuleViolation]
    scan_duration_ms: float
    total_elements_checked: int


class AccessibilityScanner:
    """Core scanner class that coordinates the accessibility testing
    process."""

    def __init__(self, rules: Optional[List[Rule]] = None):
        """Initialize scanner with optional custom rules."""
        self.rules = rules or []
        self._http_client = httpx.AsyncClient(
            timeout=30.0, follow_redirects=True
        )

    async def scan_url(self, url: str) -> ScanResult:
        """Scan a URL for accessibility violations."""
        async with self._http_client as client:
            response = await client.get(url)
            html_content = response.text
            return await self.scan_html(html_content, url=url)

    async def scan_html(
        self, html: str, url: Optional[str] = None
    ) -> ScanResult:
        """Scan HTML content for accessibility violations."""
        start_time = time.perf_counter()

        soup = BeautifulSoup(html, "html5lib")
        violations = []
        total_elements = 0

        # Process each rule
        for rule in self.rules:
            rule_violations = await rule.check(soup)
            violations.extend(rule_violations)
            total_elements += rule.elements_checked

        # Calculate duration in milliseconds
        duration_ms = (time.perf_counter() - start_time) * 1000

        return ScanResult(
            url=url,
            violations=violations,
            scan_duration_ms=duration_ms,
            total_elements_checked=total_elements,
        )

    def add_rule(self, rule: Rule) -> None:
        """Add a new rule to the scanner."""
        self.rules.append(rule)

    def remove_rule(self, rule_id: str) -> None:
        """Remove a rule from the scanner by its ID."""
        self.rules = [r for r in self.rules if r.rule_id != rule_id]

    async def close(self) -> None:
        """Clean up resources."""
        await self._http_client.aclose()
