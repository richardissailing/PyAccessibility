import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Any
import jinja2
import textwrap
from reportlab.lib.pagesizes import letter  # type: ignore
from reportlab.lib import colors  # type: ignore
from reportlab.platypus import (  # type: ignore
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import (  # type: ignore
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.units import inch  # type: ignore
from io import BytesIO

from ..rules.base import RuleViolation


class ReportGenerator:
    """Generate comprehensive accessibility reports with recommendations."""

    def __init__(self) -> None:
        template_path = Path(__file__).parent.parent / "templates"
        self.template_env: jinja2.Environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_path)),
            autoescape=True
        )

    def generate_report(
        self,
        url: str,
        violations: List[RuleViolation],
        scan_duration_ms: float,
        elements_checked: int,
        output_format: str = "html",
    ) -> Union[str, bytes]:
        """Generate a comprehensive accessibility report."""
        try:
            grouped_violations = self._group_violations(violations)
            stats: Dict[str, Union[int, float, str, Dict[str, int]]] = {
                "total_violations": len(violations),
                "scan_duration_ms": scan_duration_ms,
                "elements_checked": elements_checked,
                "timestamp": datetime.now().isoformat(),
                "severity_counts": self._count_severities(violations),
                "compliance_score": self._calculate_compliance_score(
                    violations, elements_checked
                ),
            }

            if output_format == "pdf":
                return self._generate_pdf_report(
                    url, stats, violations, grouped_violations
                )
            elif output_format == "html":
                return self._generate_html_report(
                    url, stats, violations, grouped_violations
                )
            elif output_format == "json":
                return self._generate_json_report(url, stats, violations)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")

        except Exception as e:
            raise Exception(f"Failed to generate report: {str(e)}")

    def _generate_pdf_report(
        self,
        url: str,
        stats: Dict[str, Any],
        violations: List[RuleViolation],
        grouped_violations: Dict[str, List[RuleViolation]]
    ) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        def clean_html_text(text: str) -> str:
            # Remove HTML tags and escape special characters
            text = text.replace('&', '&amp;')
            text = text.replace('<', '&lt;')
            text = text.replace('>', '&gt;')
            text = text.replace('"', '&quot;')
            text = text.replace("'", '&#39;')
            return text

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='SmallText',
            parent=styles['Normal'],
            fontSize=8,
            leading=10
        ))
        styles.add(ParagraphStyle(
            name='CodeText',
            parent=styles['SmallText'],
            fontName='Courier',
            backColor=colors.lightgrey,
            spaceAfter=10
        ))

        elements = []

        # Title and Header
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        elements.append(Paragraph("Accessibility Report", title_style))
        elements.append(Paragraph(f"URL: {url}", styles["Normal"]))
        elements.append(Spacer(1, 20))

        # Summary
        elements.append(Paragraph("Summary", styles["Heading2"]))
        elements.append(Spacer(1, 10))

        summary_data = [
            ["Metric", "Value"],
            ["Total Violations", str(stats["total_violations"])],
            ["Elements Checked", str(stats["elements_checked"])],
            ["Scan Duration", f"{stats['scan_duration_ms']:.2f}ms"],
            ["Compliance Score", f"{stats['compliance_score']:.1f}%"],
        ]
        summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))

        # Severity Distribution
        elements.append(
            Paragraph("Violations by Severity", styles["Heading3"])
        )
        elements.append(Spacer(1, 10))

        severity_data = [
            ["Severity", "Count"],
        ] + [[k.title(), str(v)] for k, v in stats["severity_counts"].items()]
        severity_table = Table(severity_data, colWidths=[2*inch, 3*inch])
        severity_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(severity_table)
        elements.append(Spacer(1, 20))

        # Detailed Violations
        elements.append(Paragraph("Detailed Violations", styles["Heading2"]))
        elements.append(Spacer(1, 10))

        for criterion, group_violations in grouped_violations.items():
            elements.append(
                Paragraph(f"WCAG Criterion: {criterion}", styles["Heading3"])
            )

            for violation in group_violations:
                elements.append(Spacer(1, 10))

                # Add violation details as separate paragraphs
                elements.append(
                    Paragraph(
                        f"Rule ID: {violation.rule_id}",
                        styles["Heading4"]
                    )
                )
                elements.append(
                    Paragraph(
                        f"Severity: {violation.severity.title()}",
                        styles["Normal"]
                    )
                )
                elements.append(
                    Paragraph(
                        f"Description: {violation.description}",
                        styles["Normal"]
                    )
                )

                if violation.suggested_fix:
                    elements.append(
                        Paragraph(
                            f"Suggested Fix: {violation.suggested_fix}",
                            styles["Normal"]
                        )
                    )

                if violation.element:
                    elements.append(Paragraph("Element:", styles["Normal"]))
                    # Clean and format the element text
                    element_text = clean_html_text(violation.element)
                    if len(element_text) > 100:
                        # Wrap long lines
                        wrapped_text = textwrap.fill(element_text, width=100)
                    else:
                        wrapped_text = element_text

                    # Use a monospace font style without background color
                    code_style = ParagraphStyle(
                        'Code',
                        parent=styles['Normal'],
                        fontName='Courier',
                        fontSize=8,
                        leading=10,
                        spaceAfter=10
                    )
                    elements.append(Paragraph(wrapped_text, code_style))

                elements.append(Spacer(1, 10))
                elements.append(Paragraph("<hr/>", styles["Normal"]))

        doc.build(elements)
        return buffer.getvalue()

    def _generate_html_report(
        self,
        url: str,
        stats: Dict[str, Any],
        violations: List[RuleViolation],
        grouped_violations: Dict[str, List[RuleViolation]]
    ) -> str:
        try:
            template = self.template_env.get_template("report.html")
            return template.render(
                url=url,
                stats=stats,
                violations=violations,
                grouped_violations=grouped_violations,
            )
        except jinja2.TemplateNotFound:
            raise Exception(
                "HTML template not found. Ensure report.html exists in/"
                "templates directory."
            )
        except jinja2.TemplateError as e:
            raise Exception(f"Template rendering error: {str(e)}")

    def _generate_json_report(
        self,
        url: str,
        stats: Dict[str, Any],
        violations: List[RuleViolation]
    ) -> str:
        report_data: Dict[str, Any] = {
            "url": url,
            "stats": stats,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "severity": v.severity,
                    "description": v.description,
                    "element": v.element,
                    "wcag_criterion": v.wcag_criterion,
                    "suggested_fix": v.suggested_fix,
                }
                for v in violations
            ],
        }
        return json.dumps(report_data, indent=2)

    def _calculate_compliance_score(
        self,
        violations: List[RuleViolation],
        elements_checked: int
    ) -> float:
        if not elements_checked:
            return 100.0

        severity_weights = {
            "critical": 1.0,
            "error": 0.7,
            "warning": 0.3,
            "info": 0.1
        }

        weighted_violations = sum(
            severity_weights.get(v.severity, 0.5) for v in violations
        )

        score = max(0, 100 - (weighted_violations / elements_checked * 100))
        return round(score, 2)

    def _group_violations(
        self,
        violations: List[RuleViolation]
    ) -> Dict[str, List[RuleViolation]]:
        grouped: Dict[str, List[RuleViolation]] = {}
        for violation in violations:
            criterion = violation.wcag_criterion or "other"
            if criterion not in grouped:
                grouped[criterion] = []
            grouped[criterion].append(violation)
        return grouped

    def _count_severities(
        self,
        violations: List[RuleViolation]
    ) -> Dict[str, int]:
        counts: Dict[str, int] = {
            "critical": 0,
            "error": 0,
            "warning": 0,
            "info": 0
        }
        for violation in violations:
            counts[violation.severity] = counts.get(violation.severity, 0) + 1
        return counts
