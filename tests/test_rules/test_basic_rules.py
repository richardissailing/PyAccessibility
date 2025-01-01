import pytest
from bs4 import BeautifulSoup

from pyaccessibility.rules.basic_rules import (
    ColorContrastRule,
    FormLabelRule,
    ImgAltTextRule,
    HeadingHierarchyRule,
)


@pytest.mark.asyncio
class TestImgAltTextRule:
    async def test_missing_alt_text(self) -> None:
        rule = ImgAltTextRule()
        html = '<img src="test.jpg">'
        soup = BeautifulSoup(
            html, "html5lib"
        )
        violations = await rule.check(soup)

        assert len(violations) == 1
        assert violations[0].severity == "error"
        assert "missing alt text" in violations[0].description.lower()

    async def test_empty_alt_text(self) -> None:
        rule = ImgAltTextRule()
        html = '<img src="test.jpg" alt="">'
        soup = BeautifulSoup(html, "html5lib")

        violations = await rule.check(soup)

        assert len(violations) == 1
        assert "uninformative alt text" in violations[0].description.lower(
        )

    async def test_uninformative_alt_text(self) -> None:
        rule = ImgAltTextRule()
        for bad_alt in ["image", "photo", "picture", "img", "*"]:
            html = f'<img src="test.jpg" alt="{bad_alt}">'
            soup = BeautifulSoup(html, "html5lib")

            violations = await rule.check(soup)

            assert len(violations) == 1
            assert "uninformative alt text" in violations[0].description.lower(
            )

    async def test_filename_as_alt(self) -> None:
        rule = ImgAltTextRule()
        html = '<img src="test.jpg" alt="test.jpg">'
        soup = BeautifulSoup(html, "html5lib")

        violations = await rule.check(soup)

        assert len(violations) == 1
        assert "filename" in violations[0].description.lower()

    async def test_long_alt_text(self) -> None:
        rule = ImgAltTextRule()
        long_text = "a" * 126  # Longer than 125 characters
        html = f'<img src="test.jpg" alt="{long_text}">'
        soup = BeautifulSoup(html, "html5lib")

        violations = await rule.check(soup)

        assert len(violations) == 1
        assert "too long" in violations[0].description.lower()

    async def test_decorative_image(self) -> None:
        rule = ImgAltTextRule()
        html = '<img src="test.jpg" role="presentation" alt="decorative">'
        soup = BeautifulSoup(html, "html5lib")

        violations = await rule.check(soup)

        assert len(violations) == 1
        assert "decorative image" in violations[0].description.lower()

    async def test_valid_alt_text(self) -> None:
        rule = ImgAltTextRule()
        html = (
            '<img src="test.jpg" '
            'alt="A red car parked in front of a building">'
        )
        soup = BeautifulSoup(html, "html5lib")

        violations = await rule.check(soup)

        assert len(violations) == 0


@pytest.mark.asyncio
class TestColorContrastRule:
    async def test_insufficient_contrast(self) -> None:
        rule = ColorContrastRule()
        html = (
            '<p style="color: #777; background-color: #fff;">'
            'Low contrast text</p>'
        )
        soup = BeautifulSoup(html, "html5lib")

        violations = await rule.check(soup)

        assert len(violations) == 1
        assert "contrast ratio" in violations[0].description.lower()

    async def test_sufficient_contrast(self) -> None:
        rule = ColorContrastRule()
        html = (
            '<p style="color: #000; background-color: #fff;">'
            'Good contrast</p>'
        )
        soup = BeautifulSoup(html, "html5lib")

        violations = await rule.check(soup)

        assert len(violations) == 0

    async def test_missing_colors(self) -> None:
        rule = ColorContrastRule()
        html = "<p>Text without explicit colors</p>"
        soup = BeautifulSoup(html, "html5lib")

        violations = await rule.check(soup)

        assert len(violations) == 0


@pytest.mark.asyncio
class TestFormLabelRule:
    async def test_missing_label(self) -> None:
        rule = FormLabelRule()
        html = '<input type="text" name="username">'
        soup = BeautifulSoup(html, "html5lib")

        violations = await rule.check(soup)

        assert len(violations) == 1
        assert "lacks a proper label" in violations[0].description.lower()

    async def test_aria_label(self) -> None:
        rule = FormLabelRule()
        html = '<input type="text" aria-label="Username">'
        soup = BeautifulSoup(html, "html5lib")

        violations = await rule.check(soup)

        assert len(violations) == 0

    async def test_associated_label(self) -> None:
        rule = FormLabelRule()
        html = """
            <label for="username">Username</label>
            <input type="text" id="username">
        """
        soup = BeautifulSoup(html, "html5lib")

        violations = await rule.check(soup)

        assert len(violations) == 0

    async def test_hidden_input(self) -> None:
        rule = FormLabelRule()
        html = '<input type="hidden" name="csrf_token">'
        soup = BeautifulSoup(html, "html5lib")

        violations = await rule.check(soup)

        assert len(violations) == 0


@pytest.mark.asyncio
class TestHeadingHierarchyRule:
    async def test_skipped_heading_level(self) -> None:
        rule = HeadingHierarchyRule()
        html = '<h1>Title</h1><h3>Subtitle</h3>'
        soup = BeautifulSoup(html, 'html5lib')
        violations = await rule.check(soup)
        assert len(violations) == 1
        assert "skipped heading level" in violations[0].description.lower()

    async def test_valid_heading_hierarchy(self) -> None:
        rule = HeadingHierarchyRule()
        html = '<h1>Title</h1><h2>Subtitle</h2><h2>Another</h2>'
        soup = BeautifulSoup(html, 'html5lib')
        violations = await rule.check(soup)
        assert len(violations) == 0

    async def test_multiple_h1(self) -> None:
        rule = HeadingHierarchyRule()
        html = '<h1>First</h1><h1>Second</h1>'
        soup = BeautifulSoup(html, 'html5lib')
        violations = await rule.check(soup)
        assert len(violations) == 1
        assert "multiple h1" in violations[0].description.lower()
