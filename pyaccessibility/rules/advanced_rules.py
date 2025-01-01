from typing import List, Set

from bs4 import BeautifulSoup

from .base import Rule, RuleViolation


class AriaRolesRule(Rule):
    """Check for proper ARIA roles and attributes usage."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="aria-roles",
            description="ARIA roles and attributes must be used correctly",
        )
        self.valid_roles: Set[str] = {
            "alert",
            "alertdialog",
            "button",
            "checkbox",
            "dialog",
            "gridcell",
            "link",
            "log",
            "marquee",
            "menuitem",
            "menuitemcheckbox",
            "menuitemradio",
            "option",
            "progressbar",
            "radio",
            "scrollbar",
            "slider",
            "spinbutton",
            "status",
            "tab",
            "tabpanel",
            "textbox",
            "timer",
            "tooltip",
            "treeitem",
            "combobox",
            "grid",
            "listbox",
            "menu",
            "menubar",
            "radiogroup",
            "tablist",
            "tree",
            "treegrid",
        }

    async def check(self, soup: BeautifulSoup) -> List[RuleViolation]:
        violations = []
        elements_with_role = soup.find_all(attrs={"role": True})
        self.elements_checked = len(elements_with_role)

        for element in elements_with_role:
            role = element.get("role").lower()

            # Check for invalid roles
            if role not in self.valid_roles:
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="error",
                        element=str(element),
                        description=(
                            f"Invalid ARIA role: '{role}'"
                        ),
                        wcag_criterion="4.1.2",
                        suggested_fix=(
                            f"Use a valid ARIA role from: "
                            f"{', '.join(sorted(self.valid_roles))}"
                        ),
                    )
                )

            # Check for required attributes based on role
            if role == "button" and not element.get("aria-pressed"):
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="warning",
                        element=str(element),
                        description=(
                            "Button role should have aria-pressed state"
                        ),
                        wcag_criterion="4.1.2",
                        suggested_fix=(
                            "Add aria-pressed attribute to button role"
                        ),
                    )
                )

        return violations


class KeyboardNavigationRule(Rule):
    """Check for keyboard accessibility issues."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="keyboard-nav",
            description="Elements must be keyboard accessible",
        )
        self.interactive_elements: Set[str] = {
            "a", "button", "input", "select", "textarea"
        }

    async def check(self, soup: BeautifulSoup) -> List[RuleViolation]:
        violations = []
        interactive_elements = soup.find_all(self.interactive_elements)
        elements_with_click = soup.find_all(attrs={"onclick": True})
        elements_with_role = soup.find_all(
            attrs={"role": lambda x: x in {"button", "link"}}
        )
        elements_with_tabindex = soup.find_all(attrs={"tabindex": True})

        all_elements = list(
            set(
                interactive_elements + elements_with_click +
                elements_with_role + elements_with_tabindex
            )
        )
        self.elements_checked = len(all_elements)

        for element in all_elements:
            # Check tabindex values
            tabindex = element.get("tabindex")
            if tabindex and int(tabindex) < 0:
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="error",
                        element=str(element),
                        description=(
                            "Negative tabindex prevents keyboard focus"
                        ),
                        wcag_criterion="2.1.1",
                        suggested_fix="Remove negative tabindex or set to 0",
                    )
                )

            # Check for click handlers without keyboard handlers
            if element.get("onclick") and not (
                element.get("onkeypress") or element.get("onkeydown")
            ):
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="error",
                        element=str(element),
                        description="Click handler without keyboard handler",
                        wcag_criterion="2.1.1",
                        suggested_fix=(
                            "Add onkeypress or onkeydown handler for keyboard "
                            "users"
                            )
                        ),
                    )

        return violations


class SemanticStructureRule(Rule):
    """Check for proper semantic HTML structure."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="semantic-structure",
            description="HTML must use proper semantic structure",
        )

    def _has_main_landmark(self, soup: BeautifulSoup) -> bool:
        """Check if the document has a main landmark."""
        return bool(
            soup.find("main") or
            soup.find(attrs={"role": "main"})
        )

    def _is_full_document(self, soup: BeautifulSoup) -> bool:
        """Check if this is a complete HTML document."""
        return bool(soup.find("html"))

    async def check(self, soup: BeautifulSoup) -> List[RuleViolation]:
        violations = []
        self.elements_checked = 0

        # Only check for main landmark in full HTML documents
        if self._is_full_document(soup) and not self._has_main_landmark(soup):
            violations.append(
                RuleViolation(
                    rule_id=self.rule_id,
                    severity="error",
                    element="document",
                    description="No main landmark found",
                    wcag_criterion="1.3.1",
                    suggested_fix=(
                        "Add <main> element or role='main' to primary content"
                    ),
                )
            )
            self.elements_checked += 1

        # Check for proper list structure
        lists = soup.find_all(["ul", "ol"])
        for list_elem in lists:
            invalid_children = [
                child
                for child in list_elem.children
                if child.name and child.name != "li"
            ]
            if invalid_children:
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="error",
                        element=str(list_elem),
                        description="List contains non-li elements",
                        wcag_criterion="1.3.1",
                        suggested_fix=(
                            "Ensure lists only contain <li> elements"
                        ),
                    )
                )

        self.elements_checked += len(lists)
        return violations
