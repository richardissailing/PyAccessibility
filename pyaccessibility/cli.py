import asyncio
import sys
from typing import List, Optional, Tuple, Union
from rich.progress import Progress, TaskID

import click
import httpx
from rich.console import Console

from .reports.generator import ReportGenerator
from .rules.basic_rules import ImgAltTextRule
from .rules.focus_rules import (
    FocusIndicatorRule,
    LanguageRule,
    TableAccessibilityRule,
)
from .scanner import AccessibilityScanner, ScanResult

console = Console()


def create_scanner(rules: Optional[List[str]] = None) -> AccessibilityScanner:
    """Create scanner with specified rules."""
    available_rules = {
        "img-alt": ImgAltTextRule,
        "focus": FocusIndicatorRule,
        "language": LanguageRule,
        "table": TableAccessibilityRule,
    }

    if not rules:
        rule_instances = [rule() for rule in available_rules.values()]
    else:
        valid_rules = []
        for rule in rules:
            if rule in available_rules:
                valid_rules.append(available_rules[rule]())
            else:
                console.print(
                    f"[yellow]Warning: Unknown rule '{rule}' "
                    f"will be ignored[/yellow]"
                )

        if not valid_rules:
            console.print(
                "[yellow]Warning: No rules selected. "
                "Using all available rules.[/yellow]"
            )
            valid_rules = [rule() for rule in available_rules.values()]

        rule_instances = valid_rules

    return AccessibilityScanner(rule_instances)


def format_text_report(result: ScanResult, target: str) -> str:
    """Format scan results as human-readable text."""
    lines = []
    lines.append(f"\nAccessibility Scan Results for: {target}")
    lines.append(f"Elements checked: {result.total_elements_checked}")
    lines.append(f"Scan duration: {result.scan_duration_ms:.2f}ms")
    lines.append(f"\nFound {len(result.violations)} accessibility violations:")

    if result.violations:
        for i, violation in enumerate(result.violations, 1):
            lines.append(f"\n{i}. Rule: {violation.rule_id}")
            lines.append(f"   Severity: {violation.severity}")
            lines.append(f"   Description: {violation.description}")
            if violation.element:
                lines.append(f"   Element: {violation.element}")
            if violation.help_url:
                lines.append(f"   More info: {violation.help_url}")
    else:
        lines.append("\nNo violations found!")

    return "\n".join(lines)


@click.group()
def cli() -> None:
    """PyAccessibility - Web Accessibility Testing Tool"""
    pass


@cli.command()
@click.argument("target")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["html", "json", "text", "pdf"]),
    default="text",
    help="Output format",
)
@click.option("--rules", "-r", multiple=True, help="Specific rules to check")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed progress")
@click.option("--email", help="Email address to send report to")
@click.option("--smtp-host", help="SMTP server host")
@click.option("--smtp-port", type=int, help="SMTP server port")
@click.option("--smtp-user", help="SMTP username")
@click.option("--smtp-password", help="SMTP password")
def scan(
    target: str,
    format: str,
    rules: Tuple[str, ...],
    output: Optional[str],
    verbose: bool,
    email: Optional[str] = None,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None
) -> None:
    """Scan a URL or HTML file for accessibility issues."""
    scanner = None
    try:
        scanner = create_scanner(list(rules) if rules else None)

        with Progress() as progress:
            task_id: TaskID = progress.add_task("[cyan]Scanning...", total=100)

            if verbose:
                console.print(
                    "[green]Created scanner with "
                    f"{len(scanner.rules)} rules[/green]"
                )

            # Check if file exists before scanning
            if not target.startswith(("http://", "https://")):
                try:
                    with open(target, "r", encoding="utf-8") as f:
                        pass
                except IOError:
                    console.print(
                        f"[red]Error reading file:[/red] "
                        f"File not found: {target}"
                    )
                    sys.exit(1)  # Exit with error code for invalid file

            # Run the scan
            try:
                result = asyncio.run(
                    scan_target(scanner, target, progress, task_id)
                )
                if not result:
                    sys.exit(1)  # Exit with error code if scan fails

                progress.update(task_id, completed=70)

                if verbose:
                    console.print(
                        "[green]Scan complete.[/green] "
                        f"Found {len(result.violations)} violations"
                    )

                # Generate report
                report: Union[str, bytes]
                if format == "text":
                    report = format_text_report(result, target)
                else:
                    try:
                        generator = ReportGenerator()
                        report = generator.generate_report(
                            url=target,
                            violations=result.violations,
                            scan_duration_ms=result.scan_duration_ms,
                            elements_checked=result.total_elements_checked,
                            output_format=format,
                        )
                    except Exception as e:
                        console.print("[red]Error generating report:[/red]")
                        console.print(str(e))
                        if verbose:
                            import traceback
                            console.print(traceback.format_exc())
                        # Exit with error code for report generation failure
                        sys.exit(1)

                progress.update(task_id, completed=90)

                # In the scan function where you handle the output:
                if output:
                    try:
                        mode = "wb" if isinstance(report, bytes) else "w"
                        encoding = None if isinstance(report, bytes) else \
                            "utf-8"

                        with open(output, mode, encoding=encoding) as f:
                            if isinstance(report, bytes):
                                f.write(report)
                            else:
                                f.write(report)

                        console.print(
                            f"[green]Report saved to {output}[/green]"
                        )
                    except IOError as e:
                        console.print(
                            f"[red]Error saving report:[/red] {str(e)}"
                        )
                        sys.exit(1)
                else:
                    if format != "pdf":  # Don't print binary PDF to console
                        click.echo(report)

                violation_count = len(result.violations)
                if violation_count > 0:
                    console.print(
                        f"Found {violation_count} accessibility violations"
                    )
                else:
                    console.print("No accessibility violations found")

            except httpx.HTTPError as e:
                console.print("[red]HTTP Error:[/red] Failed to fetch", target)
                console.print("[red]Details:[/red]", str(e))
                sys.exit(1)  # Exit with error code for HTTP error
            except Exception as e:
                console.print("[red]Error during scan:[/red]", str(e))
                if verbose:
                    import traceback
                    console.print(traceback.format_exc())
                sys.exit(1)  # Exit with error code for scan error

    except Exception as e:
        console.print("[red]Unexpected error:[/red]", str(e))
        sys.exit(1)  # Exit with error code for unexpected errors
    finally:
        if scanner:
            try:
                asyncio.run(scanner.close())
            except Exception:
                pass


async def scan_target(
    scanner: AccessibilityScanner,
    target: str,
    progress: Progress,
    task_id: TaskID,
) -> Optional[ScanResult]:
    """Scan a target (URL or file)."""
    progress.update(task_id, completed=30)

    if target.startswith(("http://", "https://")):
        return await scanner.scan_url(target)
    else:
        try:
            with open(target, "r", encoding="utf-8") as f:
                html_content = f.read()
            return await scanner.scan_html(html_content)
        except IOError as e:
            console.print(f"[red]Error reading file:[/red] {str(e)}")
            return None


@cli.command()
def list_rules() -> None:
    """List all available accessibility rules."""
    rules = {
        "img-alt": "Check for proper image alt text",
        "focus": "Check for visible focus indicators",
        "language": "Validate language declarations",
        "table": "Check table structure and headers",
    }

    console.print("\n[bold]Available Rules:[/bold]")
    console.print("\n[bold]Rule ID[/bold]            [bold]Description[/bold]")
    console.print("-" * 50)  # Add a separator line
    for rule_id, description in rules.items():
        # Pad rule_id to 20 characters for alignment
        console.print(f"  {rule_id:<18} {description}")


if __name__ == "__main__":
    cli()
