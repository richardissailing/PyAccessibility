from dataclasses import dataclass
from typing import List, Optional

from bs4 import BeautifulSoup


@dataclass
class RuleViolation:
    """Represents a single accessibility violation."""

    rule_id: str
    severity: str
    element: str
    description: str
    wcag_criterion: Optional[str] = None
    suggested_fix: Optional[str] = None
    help_url: Optional[str] = None


class Rule:
    """Base class for accessibility rules."""

    def __init__(self, rule_id: str, description: str):
        self.rule_id = rule_id
        self.description = description
        self.elements_checked = 0

    async def check(self, soup: BeautifulSoup) -> List[RuleViolation]:
        """Check HTML content for violations of this rule."""
        raise NotImplementedError("Rule classes must implement check method")
