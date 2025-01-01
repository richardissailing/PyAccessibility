from typing import List, Optional, Any
import httpx
import pytest
from bs4 import BeautifulSoup

from pyaccessibility.rules.base import Rule, RuleViolation
from pyaccessibility.scanner import AccessibilityScanner


class MockRule(Rule):
    def __init__(
        self,
        rule_id: str,
        violations: Optional[List[RuleViolation]] = None
    ) -> None:
        super().__init__(rule_id=rule_id, description="Mock rule for testing")
        self.violations_to_return = violations or []

    async def check(self, soup: BeautifulSoup) -> List[RuleViolation]:
        return self.violations_to_return


class MockResponse:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code


@pytest.mark.asyncio
async def test_scanner_empty_rules() -> None:
    scanner = AccessibilityScanner([])
    html = "<html><body><p>Test content</p></body></html>"

    result = await scanner.scan_html(html)

    assert len(result.violations) == 0
    assert result.total_elements_checked == 0
    await scanner.close()


@pytest.mark.asyncio
async def test_scanner_with_mock_rule() -> None:
    mock_violation = RuleViolation(
        rule_id="mock-rule",
        severity="error",
        element="<div>test</div>",
        description="Mock violation",
    )
    mock_rule = MockRule("mock-rule", [mock_violation])

    scanner = AccessibilityScanner([mock_rule])
    html = "<html><body><div>test</div></body></html>"

    result = await scanner.scan_html(html)

    assert len(result.violations) == 1
    assert result.violations[0].rule_id == "mock-rule"
    await scanner.close()


@pytest.mark.asyncio
async def test_scanner_multiple_rules() -> None:
    rule1 = MockRule(
        "rule1",
        [
            RuleViolation(
                rule_id="rule1",
                severity="error",
                element="<div>test1</div>",
                description="Violation 1",
            )
        ],
    )
    rule2 = MockRule(
        "rule2",
        [
            RuleViolation(
                rule_id="rule2",
                severity="warning",
                element="<div>test2</div>",
                description="Violation 2",
            )
        ],
    )

    scanner = AccessibilityScanner([rule1, rule2])
    html = "<html><body><div>test</div></body></html>"

    result = await scanner.scan_html(html)

    assert len(result.violations) == 2
    assert {v.rule_id for v in result.violations} == {"rule1", "rule2"}
    await scanner.close()


@pytest.mark.asyncio
async def test_add_remove_rule() -> None:
    scanner = AccessibilityScanner([])
    mock_rule = MockRule("test-rule")

    scanner.add_rule(mock_rule)
    assert len(scanner.rules) == 1

    scanner.remove_rule("test-rule")
    assert len(scanner.rules) == 0
    await scanner.close()


@pytest.mark.asyncio
async def test_scanner_url_request(monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_get(*args: Any, **kwargs: Any) -> MockResponse:
        return MockResponse("<html><body><p>Test content</p></body></html>")

    # Mock httpx.AsyncClient.get
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    mock_rule = MockRule(
        "test-rule",
        [
            RuleViolation(
                rule_id="test-rule",
                severity="error",
                element="<p>Test content</p>",
                description="Test violation",
            )
        ],
    )

    scanner = AccessibilityScanner([mock_rule])
    result = await scanner.scan_url("https://example.com")

    assert len(result.violations) == 1
    assert result.url == "https://example.com"
    await scanner.close()


@pytest.mark.asyncio
async def test_scanner_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_get(*args: Any, **kwargs: Any) -> None:
        raise httpx.HTTPError("Mock HTTP error")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    scanner = AccessibilityScanner([])

    with pytest.raises(httpx.HTTPError):
        await scanner.scan_url("https://example.com")

    await scanner.close()


@pytest.mark.asyncio
async def test_scanner_invalid_html() -> None:
    scanner = AccessibilityScanner([])
    invalid_html = "<not>valid</html>"

    result = await scanner.scan_html(invalid_html)

    assert result.violations == []
    assert result.scan_duration_ms > 0
    await scanner.close()
