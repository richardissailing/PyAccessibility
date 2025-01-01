import pytest
from click.testing import CliRunner
from pathlib import Path
from pyaccessibility.cli import scan, list_rules


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def sample_html_file(tmp_path: Path) -> Path:
    test_file = tmp_path / "test.html"
    test_file.write_text("""
        <html>
            <body>
                <img src="test.jpg">
                <h1>Title</h1>
                <h3>Subtitle</h3>
            </body>
        </html>
    """)
    return test_file


def test_scan_with_output_file(
    runner: CliRunner, sample_html_file: Path, tmp_path: Path
) -> None:
    output_file = tmp_path / "report.json"
    result = runner.invoke(scan, [
        str(sample_html_file),
        '--output', str(output_file),
        '--format', 'json'
    ])
    assert result.exit_code == 0
    assert output_file.exists()
    assert output_file.read_text()


def test_scan_with_specific_rules(
    runner: CliRunner, sample_html_file: Path
) -> None:
    result = runner.invoke(scan, [
        str(sample_html_file),
        '--rules', 'img-alt',
        '--rules', 'focus'
    ])
    assert result.exit_code == 0
    # Check for presence of scan results rather than specific rule names
    assert "violations" in result.output.lower()


def test_scan_with_invalid_rule(
    runner: CliRunner, sample_html_file: Path
) -> None:
    result = runner.invoke(scan, [
        str(sample_html_file),
        '--rules', 'nonexistent-rule'
    ])
    # Should not fail, just warn and use all rules
    assert result.exit_code == 0
    assert "Warning: No rules selected" in result.output


def test_scan_with_verbose(runner: CliRunner, sample_html_file: Path) -> None:
    result = runner.invoke(scan, [str(sample_html_file), '--verbose'])
    assert result.exit_code == 0
    assert "Created scanner with" in result.output
    assert "Scan complete" in result.output


def test_list_rules(runner: CliRunner) -> None:
    result = runner.invoke(list_rules)
    assert result.exit_code == 0
    assert "Rule ID" in result.output
    assert "img-alt" in result.output
    assert "focus" in result.output
    assert "language" in result.output
    assert "table" in result.output


def test_scan_with_format_option(
    runner: CliRunner, sample_html_file: Path
) -> None:
    result = runner.invoke(scan, [
        str(sample_html_file),
        '--format', 'json'
    ])
    assert result.exit_code == 0


def test_scan_invalid_file(runner: CliRunner) -> None:
    result = runner.invoke(scan, ['nonexistent.html'])
    assert result.exit_code == 1
    assert "Error reading file" in result.output


def test_scan_empty_rules(runner: CliRunner, sample_html_file: Path) -> None:
    result = runner.invoke(scan, [
        str(sample_html_file),
        '--rules'
    ])
    assert result.exit_code == 2  # Click shows usage error for missing value
