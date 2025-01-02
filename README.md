# PyAccessibility

A comprehensive web accessibility testing tool that helps identify and fix accessibility issues in web pages.

## Features

* Automated accessibility testing
* WCAG 2.1 compliance checks
* HTML parsing and analysis
* Detailed violation reporting
* Multiple output formats (HTML, JSON)

Extensive rule set including:
* Image alt text validation
* Color contrast analysis
* ARIA roles validation
* Keyboard navigation checks
* Semantic structure analysis
* Form accessibility testing

## Currently Implemented Rules

### Image Alt Text (ImgAltTextRule)

* Checks for missing alt text
* Validates alt text quality
* Identifies decorative images

### Color Contrast (ColorContrastRule)

* Verifies text contrast ratios
* Checks background/foreground combinations
* Supports WCAG AA standards

### Semantic Structure (SemanticStructureRule)
* Validates proper HTML structure
* Checks for main landmarks
* Ensures proper list usage

### ARIA Roles (AriaRolesRule)
* Validates ARIA role usage
* Checks required attributes
* Ensures proper role combinations

### Keyboard Navigation (KeyboardNavigationRule)
* Checks focus management
* Validates keyboard handlers
* Identifies focus traps

## Installation

1. Ensure you have Python 3.9+ installed
2. Install Poetry (dependency management tool):

``` bash
curl -sSL https://install.python-poetry.org | python3 -
```
3. Clone the repository and install dependencies:
``` bash
git clone https://github.com/richardissailing/PyAccessibility
cd pyaccessibility
poetry install
```

## USAGE
### Command Line Interface

```bash
# Scan a URL
poetry run pyaccessibility scan https://example.com

# Scan with specific rules
poetry run pyaccessibility scan https://example.com -r alt-text -r contrast

# Generate HTML report
poetry run pyaccessibility scan https://example.com --format html > report.html

# List available rules
poetry run pyaccessibility list-rules

# Generate and email report
poetry run pyaccessibility scan https://example.com \
    -f pdf \
    --email user@example.com \
    --smtp-host smtp.gmail.com \
    --smtp-port 587 \
    --smtp-user your@gmail.com \
    --smtp-password "your-password"

# Using environment variables for SMTP config
export PYACCESSIBILITY_SMTP_HOST=smtp.gmail.com
export PYACCESSIBILITY_SMTP_PORT=587
export PYACCESSIBILITY_SMTP_USER=your@gmail.com
export PYACCESSIBILITY_SMTP_PASSWORD="your-password"

poetry run pyaccessibility scan https://example.com -f pdf --email user@example.com
```
### Python API

``` python
from pyaccessibility import AccessibilityScanner
from pyaccessibility.rules.basic_rules import ImgAltTextRule, ColorContrastRule

# Create scanner with specific rules
scanner = AccessibilityScanner([
    ImgAltTextRule(),
    ColorContrastRule()
])

# Scan a URL
async def scan_site():
    result = await scanner.scan_url("https://example.com")
    print(f"Found {len(result.violations)} violations")
    for violation in result.violations:
        print(f"- {violation.description}")

# Scan HTML content
html_content = """
<html>
    <body>
        <img src="test.jpg">  <!-- Missing alt text -->
    </body>
</html>
"""
result = await scanner.scan_html(html_content)
```

## Development

### Project Structure

```
pyaccessibility/
├── pyproject.toml
├── pyaccessibility/
│   ├── __init__.py
│   ├── cli.py
│   ├── scanner.py
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── basic_rules.py
│   │   └── advanced_rules.py
│   ├── reports/
│   │   ├── __init__.py
│   │   └── generator.py
│   └── templates/
│       └── report.html
└── tests/
    ├── __init__.py
    ├── test_rules/
    │   ├── test_basic_rules.py
    │   └── test_advanced_rules.py
    └── test_reports/
        └── test_generator.py
```

### Running Tests
Run all tests:
``` bash
poetry run pytest
```

Run specific test files:
``` bash
poetry run pytest tests/test_rules/test_basic_rules.py -v
```

Run tests with coverage:
``` bash
poetry run pytest --cov=pyaccessibility

```
Run build tests
``` bash
poetry run flake8
poetry run mypy .
```
### Adding New Rules

1. Create a new rule class in rules/basic_rules.py or rules/advanced_rules.py:
``` python
class MyNewRule(Rule):
    def __init__(self):
        super().__init__(
            rule_id="my-rule",
            description="Description of what the rule checks"
        )
    
    async def check(self, soup: BeautifulSoup) -> List[RuleViolation]:
        violations = []
        # Implement rule logic here
        return violations
```

2. Add tests in tests/test_rules/:
``` python
@pytest.mark.asyncio
async def test_my_new_rule():
    rule = MyNewRule()
    html = "<div>Test content</div>"
    soup = BeautifulSoup(html, 'html5lib')
    
    violations = await rule.check(soup)
    assert len(violations) == expected_count
```
## Contributing

Fork the repository
Create a feature branch
Add tests for new functionality
Ensure all tests pass
Submit a pull request

## License
MIT License - see LICENSE file for details