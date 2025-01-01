from typing import List, Set
from bs4 import BeautifulSoup, Tag

from .base import Rule, RuleViolation


class FocusIndicatorRule(Rule):
    """Check for proper focus indicators on interactive elements."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="focus-indicator",
            description=(
                "Interactive elements must have visible focus indicators"
            ),
        )
        self.interactive_elements: Set[str] = {
            "a",
            "button",
            "input",
            "select",
            "textarea",
            "summary",
            "details",
            "[tabindex]",
            "[contenteditable]",
        }
        self.elements_checked = 0

    async def check(self, soup: BeautifulSoup) -> List[RuleViolation]:
        violations: List[RuleViolation] = []

        # Find all interactive elements
        for tag_name in self.interactive_elements:
            elements = soup.select(tag_name)
            self.elements_checked += len(elements)

            for element in elements:
                if not isinstance(element, Tag):
                    continue  # type: ignore[unreachable]

                # Check for outline:none or outline:0
                style = str(element.get("style", "")).lower()
                style_normalized = style.replace(" ", "")

                if ("outline:none" in style_normalized or
                   "outline:0" in style_normalized):
                    violations.append(
                        RuleViolation(
                            rule_id=self.rule_id,
                            severity="error",
                            element=str(element),
                            description="Element removes focus indicator",
                            wcag_criterion="2.4.7",
                            suggested_fix=(
                                "Remove outline:none/0 and ensure focus "
                                "indicator is visible"
                            ),
                        )
                    )

                # Check for tabindex=-1
                if tabindex := element.get("tabindex"):
                    try:
                        if int(str(tabindex)) < 0:
                            violations.append(
                                RuleViolation(
                                    rule_id=self.rule_id,
                                    severity="error",
                                    element=str(element),
                                    description=(
                                        "Element is programmatically removed "
                                        "from focus order"
                                    ),
                                    wcag_criterion="2.4.7",
                                    suggested_fix=(
                                        "Remove negative tabindex unless "
                                        "deliberately managing focus"
                                    ),
                                )
                            )
                    except ValueError:
                        # Skip if tabindex value can't be converted to int
                        continue

        return violations


class LanguageRule(Rule):
    """Check for proper language declarations."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="language",
            description=(
                "Page and content must have proper language declarations"
            ),
        )
        self.valid_lang_codes: Set[str] = {
            "en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko",
        }

    async def check(self, soup: BeautifulSoup) -> List[RuleViolation]:
        violations: List[RuleViolation] = []

        # Check html lang attribute
        html_tag = soup.find("html")
        self.elements_checked += 1

        if not html_tag or not isinstance(html_tag, Tag):
            violations.append(
                RuleViolation(
                    rule_id=self.rule_id,
                    severity="error",
                    element="document",
                    description="No HTML root element found",
                    wcag_criterion="3.1.1",
                    suggested_fix=(
                        "Add proper HTML root element with lang attribute"
                    ),
                )
            )
            return violations

        lang_attr = html_tag.get("lang", "")
        lang = str(lang_attr).lower().split("-")[0] if lang_attr else ""

        if not lang:
            violations.append(
                RuleViolation(
                    rule_id=self.rule_id,
                    severity="error",
                    element=str(html_tag),
                    description="Missing language declaration",
                    wcag_criterion="3.1.1",
                    suggested_fix=(
                        'Add lang attribute to HTML element (e.g., lang="en")'
                    )
                )
            )
        elif lang not in self.valid_lang_codes:
            violations.append(
                RuleViolation(
                    rule_id=self.rule_id,
                    severity="warning",
                    element=str(html_tag),
                    description=f"Potentially invalid language code: {lang}",
                    wcag_criterion="3.1.1",
                    suggested_fix="Use valid ISO 639-1 language code",
                )
            )

        def has_lang_attr(tag: Tag) -> bool:
            return tag.get("lang") is not None

        # Check for language changes in content
        elements_with_lang = [
            tag for tag in soup.find_all(has_lang_attr)
            if isinstance(tag, Tag)
        ]
        self.elements_checked += len(elements_with_lang)

        for element in elements_with_lang:
            lang_attr = element.get("lang", "")
            element_lang = (
                str(lang_attr).lower().split("-")[0] if lang_attr else ""
            )

            if element_lang and element_lang not in self.valid_lang_codes:
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="warning",
                        element=str(element),
                        description=(
                            f"Invalid language code in content: {element_lang}"
                        ),
                        wcag_criterion="3.1.2",
                        suggested_fix="Use valid ISO 639-1 language code",
                    )
                )

        return violations


class TableAccessibilityRule(Rule):
    """Check table structure and headers for accessibility."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="table-accessibility",
            description="Tables must have proper structure and headers",
        )
        self.elements_checked = 0  # Initialize counter in __init__

    async def check(self, soup: BeautifulSoup) -> List[RuleViolation]:
        violations: List[RuleViolation] = []
        tables = soup.find_all("table")
        self.elements_checked += len(tables)

        for table in tables:
            if not isinstance(table, Tag):
                continue

            # Check for caption
            if not table.find("caption"):
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="warning",
                        element=str(table),
                        description="Table missing caption",
                        wcag_criterion="1.3.1",
                        suggested_fix=(
                            "Add <caption> element to describe table content"
                        ),
                    )
                )

            # Check for headers
            headers = table.find_all(["th"])
            if not headers:
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="error",
                        element=str(table),
                        description="Table has no header cells",
                        wcag_criterion="1.3.1",
                        suggested_fix="Add <th> elements for table headers",
                    )
                )

            # Check for scope attribute on headers
            for header in headers:
                if not isinstance(header, Tag):
                    continue
                if not header.get("scope"):
                    violations.append(
                        RuleViolation(
                            rule_id=self.rule_id,
                            severity="warning",
                            element=str(header),
                            description="Table header missing scope attribute",
                            wcag_criterion="1.3.1",
                            suggested_fix=(
                                'Add scope="col" or scope="row" to header '
                                'cells'
                            ),
                        )
                    )

            # Check for data cells without headers
            if headers:
                cells = table.find_all("td")
                for cell in cells:
                    if not isinstance(cell, Tag):
                        continue
                    parent_row = cell.find_parent("tr")
                    if not parent_row:
                        continue
                    if not (cell.get("headers") or parent_row.find("th")):
                        violations.append(
                            RuleViolation(
                                rule_id=self.rule_id,
                                severity="error",
                                element=str(cell),
                                description=(
                                    "Table cell not associated with headers"
                                ),
                                wcag_criterion="1.3.1",
                                suggested_fix=(
                                    "Ensure all data cells are associated "
                                    "with headers"
                                ),
                            )
                        )

        return violations
