import re
from typing import List, Tuple

import wcag_contrast_ratio as contrast  # type: ignore
from bs4 import BeautifulSoup

from .base import Rule, RuleViolation


class HeadingHierarchyRule(Rule):
    """Check for proper heading hierarchy (h1 -> h2 -> h3, etc.)."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="heading-hierarchy",
            description="Headings must follow proper hierarchy",
        )

    async def check(self, soup: BeautifulSoup) -> List[RuleViolation]:
        violations = []
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        self.elements_checked = len(headings)

        # Check for multiple h1 tags
        h1_headings = soup.find_all("h1")
        if len(h1_headings) > 1:
            violations.append(
                RuleViolation(
                    rule_id=self.rule_id,
                    severity="error",
                    element=str(h1_headings[1]),
                    description=(
                        "Multiple h1 headings found. Page should have only "
                        "one main heading."
                    ),
                    wcag_criterion="2.4.6",
                    suggested_fix=(
                        "Use h2-h6 for subheadings instead of multiple h1s"
                    )
                )
            )

        current_level = 0
        for heading in headings:
            level = int(heading.name[1])

            if current_level == 0 and level != 1:
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="error",
                        element=str(heading),
                        description=(
                            "First heading must be h1, found "
                            f"{heading.name}"
                        ),
                        wcag_criterion="2.4.6",
                        suggested_fix=(
                            "Change to h1 or add h1 before this heading"
                        )
                    )
                )
            elif level > current_level + 1:
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="error",
                        element=str(heading),
                        description=(
                            "Skipped heading level - found "
                            f"{heading.name} after h{current_level}"
                        ),
                        wcag_criterion="2.4.6",
                        suggested_fix=f"Change to h{current_level + 1}",
                    )
                )

            current_level = level

        return violations


class ImgAltTextRule(Rule):
    """Check for images without alt text or with uninformative alt text."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="img-alt-text",
            description="Images must have meaningful alt text"
        )
        # Common uninformative alt texts
        self.uninformative_alts = {
            "",
            "image",
            "img",
            "picture",
            "photo",
            "photograph",
            "*",
            "graphic",
            "icon",
            "picture of",
            "image of",
            "photo of",
        }

    async def check(self, soup: BeautifulSoup) -> List[RuleViolation]:
        violations = []
        images = soup.find_all("img")
        self.elements_checked = len(images)

        for img in images:
            # Check for presence of alt attribute
            if not img.has_attr("alt"):
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="error",
                        element=str(img),
                        description="Image missing alt text",
                        wcag_criterion="1.1.1",
                        suggested_fix=(
                            'Add alt="[descriptive text]" to the img element'
                        )
                    )
                )
                continue

            alt_text = img.get("alt", "").strip().lower()

            # Check for uninformative alt text
            if alt_text in self.uninformative_alts:
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="error",
                        element=str(img),
                        description=(
                            f"Image has uninformative alt text: '{img['alt']}'"
                        ),
                        wcag_criterion="1.1.1",
                        suggested_fix=(
                            "Replace with meaningful description of the image "
                            "content"
                        ),
                    )
                )

            # Check for filename as alt text
            elif any(
                ext in alt_text for ext in [".jpg", ".png", ".gif", ".webp"]
            ):
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="error",
                        element=str(img),
                        description="Image alt text appears to be a filename",
                        wcag_criterion="1.1.1",
                        suggested_fix=(
                            "Replace with meaningful description of the image "
                            "content"
                        ),
                    )
                )

            # Check for overly long alt text
            elif len(alt_text) > 125:
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="warning",
                        element=str(img),
                        description="Alt text is too long (> 125 characters)",
                        wcag_criterion="1.1.1",
                        suggested_fix=(
                            "Consider using aria-describedby for longer "
                            "descriptions"
                        ),
                    )
                )

            # Special check for decorative images
            if img.get("role") == "presentation" and alt_text:
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="warning",
                        element=str(img),
                        description=(
                            "Decorative image (role='presentation') "
                            "should have empty alt text"
                        ),
                        wcag_criterion="1.1.1",
                        suggested_fix='Set alt="" for decorative images',
                    )
                )

        return violations


class ColorContrastRule(Rule):
    """Check for sufficient color contrast between text and background."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="color-contrast",
            description=(
                "Text must have sufficient contrast with its background"
            )
        )

    def _get_color_value(self, color: str) -> Tuple[float, float, float]:
        """Convert CSS color to RGB values."""
        color = color.lower().strip()

        # Handle hex colors
        if color.startswith("#"):
            if len(color) == 4:  # Short form (#RGB)
                r = int(color[1] + color[1], 16)
                g = int(color[2] + color[2], 16)
                b = int(color[3] + color[3], 16)
            else:  # Full form (#RRGGBB)
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
            return (r / 255.0, g / 255.0, b / 255.0)

        # Handle rgb/rgba colors
        rgb_match = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", color)
        if rgb_match:
            r, g, b = map(int, rgb_match.groups())
            return (r / 255.0, g / 255.0, b / 255.0)

        # Handle named colors
        if color == "black":
            return (0.0, 0.0, 0.0)
        elif color == "white":
            return (1.0, 1.0, 1.0)

        return (0.0, 0.0, 0.0)  # Default to black if color format unknown

    async def check(self, soup: BeautifulSoup) -> List[RuleViolation]:
        violations = []
        text_elements = soup.find_all(
            ["p", "span", "div", "a", "h1", "h2", "h3", "h4", "h5", "h6"]
        )
        self.elements_checked = len(text_elements)

        for element in text_elements:
            style = element.get("style", "")
            color_match = re.search(r"color:\s*([^;]+)", style)
            bg_match = re.search(r"background-color:\s*([^;]+)", style)

            # Only check elements with both colors specified
            if color_match and bg_match:
                color = color_match.group(1).strip()
                bg_color = bg_match.group(1).strip()

                fg_rgb = self._get_color_value(color)
                bg_rgb = self._get_color_value(bg_color)

                try:
                    ratio = contrast.rgb(fg_rgb, bg_rgb)

                    # Check if contrast ratio meets WCAG standards
                    if ratio < 4.5:  # WCAG AA standard for normal text
                        violations.append(
                            RuleViolation(
                                rule_id=self.rule_id,
                                severity="error",
                                element=str(element),
                                description=(
                                    f"Insufficient color contrast ratio: "
                                    f"{ratio:.2f}:1 "
                                    "(minimum 4.5:1 required)"
                                ),
                                wcag_criterion="1.4.3",
                                suggested_fix=(
                                    "Adjust text or background color to "
                                    "improve contrast"
                                ),
                            )
                        )
                except Exception:
                    # If contrast calculation fails, skip this element
                    continue

        return violations


class FormLabelRule(Rule):
    """Check for form inputs with associated labels."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="form-label",
            description="Form inputs must have associated labels"
        )

    async def check(self, soup: BeautifulSoup) -> List[RuleViolation]:
        violations = []
        inputs = soup.find_all(["input", "select", "textarea"])
        self.elements_checked = len(inputs)

        for input_element in inputs:
            if input_element.get("type") == "hidden":
                continue

            input_id = input_element.get("id")
            aria_label = input_element.get("aria-label")
            aria_labelledby = input_element.get("aria-labelledby")

            if not (input_id or aria_label or aria_labelledby):
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        severity="error",
                        element=str(input_element),
                        description="Form input lacks a proper label",
                        wcag_criterion="1.3.1",
                        suggested_fix=(
                            "Add a label element with 'for' attribute, or "
                            "aria-label/aria-labelledby"
                        ),
                    )
                )
            elif input_id and not soup.find("label", attrs={"for": input_id}):
                if not (aria_label or aria_labelledby):
                    violations.append(
                        RuleViolation(
                            rule_id=self.rule_id,
                            severity="error",
                            element=str(input_element),
                            description=(
                                f"No label found for input with id "
                                f"'{input_id}'"
                            ),
                            wcag_criterion="1.3.1",
                            suggested_fix=f"Add a label with for='{input_id}'",
                        )
                    )

        return violations
