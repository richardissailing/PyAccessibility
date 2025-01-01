import pytest
from bs4 import BeautifulSoup
from pyaccessibility.rules.basic_rules import ImgAltTextRule


@pytest.mark.asyncio
async def test_missing_alt_text() -> None:
    rule = ImgAltTextRule()
    html = '<img src="test.jpg">'
    soup = BeautifulSoup(html, "html5lib")

    violations = await rule.check(soup)

    assert len(violations) == 1
    assert violations[0].rule_id == "img-alt-text"
    assert violations[0].severity == "error"
    assert "missing alt text" in violations[0].description.lower()


@pytest.mark.asyncio
async def test_uninformative_alt_text() -> None:
    rule = ImgAltTextRule()
    html = '<img src="test.jpg" alt="image">'
    soup = BeautifulSoup(html, "html5lib")

    violations = await rule.check(soup)

    assert len(violations) == 1
    assert "uninformative alt text" in violations[0].description.lower()


@pytest.mark.asyncio
async def test_filename_as_alt_text() -> None:
    rule = ImgAltTextRule()
    html = '<img src="test.jpg" alt="photo123.jpg">'
    soup = BeautifulSoup(html, "html5lib")

    violations = await rule.check(soup)

    assert len(violations) == 1
    assert "filename" in violations[0].description.lower()


@pytest.mark.asyncio
async def test_long_alt_text() -> None:
    rule = ImgAltTextRule()
    long_text = (
        "This is a very long alt text that exceeds the recommended length. "
        * 3
    )
    html = f'<img src="test.jpg" alt="{long_text}">'
    soup = BeautifulSoup(html, "html5lib")

    violations = await rule.check(soup)

    assert len(violations) == 1
    assert violations[0].severity == "warning"
    assert "too long" in violations[0].description.lower()


@pytest.mark.asyncio
async def test_decorative_image() -> None:
    rule = ImgAltTextRule()
    html = '<img src="test.jpg" role="presentation" alt="decorative image">'
    soup = BeautifulSoup(html, "html5lib")

    violations = await rule.check(soup)

    assert len(violations) == 1
    assert violations[0].severity == "warning"
    assert "decorative image" in violations[0].description.lower()


@pytest.mark.asyncio
async def test_valid_alt_text() -> None:
    rule = ImgAltTextRule()
    html = '<img src="test.jpg" alt="A red car parked in front of a building">'
    soup = BeautifulSoup(html, "html5lib")

    violations = await rule.check(soup)

    assert len(violations) == 0


@pytest.mark.asyncio
async def test_multiple_images() -> None:
    rule = ImgAltTextRule()
    html = """
    <div>
        <img src="1.jpg">
        <img src="2.jpg" alt="image">
        <img src="3.jpg" alt="A valid description">
        <img src="4.jpg" alt="photo.jpg">
    </div>
    """
    soup = BeautifulSoup(html, "html5lib")

    violations = await rule.check(soup)

    assert len(violations) == 3
