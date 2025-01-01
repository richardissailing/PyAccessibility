import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Any

import jinja2

from ..rules.base import RuleViolation


class ReportGenerator:
    """Generate comprehensive accessibility reports with recommendations."""

    def __init__(self) -> None:
        # Set up Jinja2 environment with proper package loading
        template_path = Path(__file__).parent.parent / "templates"
        self.template_env: jinja2.Environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_path)), autoescape=True
        )

    def generate_report(
        self,
        url: str,
        violations: List[RuleViolation],
        scan_duration_ms: float,
        elements_checked: int,
        output_format: str = "html",
    ) -> str:
        """Generate a comprehensive accessibility report."""
        try:
            # Group violations by WCAG criterion
            grouped_violations = self._group_violations(violations)

            # Calculate statistics
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

            if output_format == "html":
                # Render HTML report
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
                        "HTML template not found. Ensure report.html exists "
                        "in templates directory."
                    )
                except jinja2.TemplateError as e:
                    raise Exception(f"Template rendering error: {str(e)}")

            elif output_format == "json":
                # Generate JSON report
                report_data: Dict[str, Any] = {
                    "url": url,
                    "stats": {
                        "total_violations": stats["total_violations"],
                        "scan_duration_ms": stats["scan_duration_ms"],
                        "elements_checked": stats["elements_checked"],
                        "timestamp": stats["timestamp"],
                        "severity_counts": stats["severity_counts"],
                        "compliance_score": stats["compliance_score"],
                    },
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
            else:
                raise ValueError(f"Unsupported output format: {output_format}")

        except Exception as e:
            raise Exception(f"Failed to generate report: {str(e)}")

    def _calculate_compliance_score(
        self, violations: List[RuleViolation], elements_checked: int
    ) -> float:
        """Calculate accessibility compliance score."""
        if not elements_checked:
            return 100.0

        severity_weights = {
            "critical": 1.0,
            "error": 0.7,
            "warning": 0.3,
            "info": 0.1,
        }

        weighted_violations = sum(
            severity_weights.get(v.severity, 0.5) for v in violations
        )

        score = max(0, 100 - (weighted_violations / elements_checked * 100))
        return round(score, 2)

    def _group_violations(
        self, violations: List[RuleViolation]
    ) -> Dict[str, List[RuleViolation]]:
        """Group violations by WCAG criterion."""
        grouped: Dict[str, List[RuleViolation]] = {}
        for violation in violations:
            criterion = violation.wcag_criterion or "other"
            if criterion not in grouped:
                grouped[criterion] = []
            grouped[criterion].append(violation)
        return grouped

    def _count_severities(
        self, violations: List[RuleViolation]
    ) -> Dict[str, int]:
        """Count violations by severity level."""
        counts: Dict[str, int] = {
            "critical": 0,
            "error": 0,
            "warning": 0,
            "info": 0,
        }
        for violation in violations:
            counts[violation.severity] = counts.get(violation.severity, 0) + 1
        return counts
