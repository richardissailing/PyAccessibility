import pytest
from bs4 import BeautifulSoup

from pyaccessibility.rules.advanced_rules import (
    AriaRolesRule,
    KeyboardNavigationRule,
    SemanticStructureRule,
)


@pytest.mark.asyncio
async def test_aria_roles_valid() -> None:
    rule = AriaRolesRule()
    html = '<div role="button">Click me</div>'
    soup = BeautifulSoup(html, "html.parser")

    violations = await rule.check(soup)
    assert len(violations) == 1  # Warning for missing aria-pressed
    assert violations[0].severity == "warning"


@pytest.mark.asyncio
async def test_aria_roles_invalid() -> None:
    rule = AriaRolesRule()
    html = '<div role="invalid-role">Invalid</div>'
    soup = BeautifulSoup(html, "html.parser")

    violations = await rule.check(soup)
    assert len(violations) == 1
    assert violations[0].severity == "error"


@pytest.mark.asyncio
async def test_aria_roles_multiple() -> None:
    rule = AriaRolesRule()
    html = '''
        <div role="invalid-role">Invalid</div>
        <button role="button">Valid but missing aria-pressed</button>
    '''
    soup = BeautifulSoup(html, "html.parser")

    violations = await rule.check(soup)
    assert len(violations) == 2


@pytest.mark.asyncio
async def test_keyboard_navigation_tabindex() -> None:
    rule = KeyboardNavigationRule()
    html = '<button tabindex="-1">Cannot focus</button>'
    soup = BeautifulSoup(html, "html.parser")

    violations = await rule.check(soup)
    assert len(violations) == 1
    assert "tabindex" in violations[0].description.lower()


@pytest.mark.asyncio
async def test_keyboard_navigation_click_handler() -> None:
    rule = KeyboardNavigationRule()
    html = '<div onclick="handleClick()">Click me</div>'
    soup = BeautifulSoup(html, "html.parser")

    violations = await rule.check(soup)
    assert len(violations) == 1
    assert "keyboard handler" in violations[0].description.lower()


@pytest.mark.asyncio
async def test_keyboard_navigation_complete() -> None:
    rule = KeyboardNavigationRule()
    html = '''
        <button onclick="handleClick()" onkeypress="handleKey()">Good</button>
        <div tabindex="-1">Bad</div>
    '''
    soup = BeautifulSoup(html, "html.parser")

    violations = await rule.check(soup)
    assert len(violations) == 1
    assert "tabindex" in violations[0].description.lower()


@pytest.mark.asyncio
async def test_semantic_structure_lists() -> None:
    rule = SemanticStructureRule()
    html = '''
        <ul>
            <div>Invalid child</div>
            <li>Valid item</li>
        </ul>
    '''
    soup = BeautifulSoup(html, "html.parser")

    violations = await rule.check(soup)
    assert len(violations) == 1
    assert "non-li elements" in violations[0].description.lower()


@pytest.mark.asyncio
async def test_semantic_structure_complete() -> None:
    rule = SemanticStructureRule()
    html = '''
        <main>
            <ul>
                <li>Valid structure</li>
            </ul>
        </main>
    '''
    soup = BeautifulSoup(html, "html.parser")

    violations = await rule.check(soup)
    assert len(violations) == 0
