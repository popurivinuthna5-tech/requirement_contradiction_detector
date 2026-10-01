import csv
import io
import json
from typing import List, Dict, Any
from app.models.schemas import ConflictResponse, ConflictSummary

class ReportService:
    """Generates structured exports in CSV, JSON, Markdown, and Printable HTML formats."""

    @classmethod
    def generate_csv(cls, conflicts: List[ConflictResponse]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Conflict ID",
            "Conflict Type",
            "Severity",
            "Similarity Score",
            "Requirement 1 ID",
            "Requirement 1 Document",
            "Requirement 1 Section",
            "Requirement 1 Page",
            "Requirement 1 Text",
            "Requirement 2 ID",
            "Requirement 2 Document",
            "Requirement 2 Section",
            "Requirement 2 Page",
            "Requirement 2 Text",
            "Conflicting Elements",
            "Explanation",
            "Suggested Clarification"
        ])
        
        for c in conflicts:
            writer.writerow([
                c.conflict_id,
                c.conflict_type,
                c.severity,
                f"{c.similarity_score:.2f}",
                c.requirement_1.reference_code,
                c.requirement_1.source_document,
                c.requirement_1.section,
                c.requirement_1.page_number or "N/A",
                c.requirement_1.requirement_text,
                c.requirement_2.reference_code,
                c.requirement_2.source_document,
                c.requirement_2.section,
                c.requirement_2.page_number or "N/A",
                c.requirement_2.requirement_text,
                c.conflicting_elements or "",
                c.explanation,
                c.suggested_clarification or ""
            ])
            
        return output.getvalue()

    @classmethod
    def generate_json(cls, summary: ConflictSummary, conflicts: List[ConflictResponse]) -> str:
        data = {
            "summary": summary.model_dump(),
            "conflicts": [c.model_dump() for c in conflicts]
        }
        return json.dumps(data, indent=2)

    @classmethod
    def generate_markdown(cls, summary: ConflictSummary, conflicts: List[ConflictResponse]) -> str:
        lines = []
        lines.append("# Software Requirements Conflict & Overlap Analysis Report")
        lines.append("\n## Executive Summary\n")
        lines.append(f"- **Total Documents Analyzed:** {summary.total_documents}")
        lines.append(f"- **Total Extracted Requirements:** {summary.total_requirements}")
        lines.append(f"- **Total Detected Conflicts/Relationships:** {summary.total_relationships}")
        lines.append(f"  - **Critical Contradictions:** {summary.critical_conflicts}")
        lines.append(f"  - **High Severity Conflicts:** {summary.high_conflicts}")
        lines.append(f"  - **Medium Severity Conflicts:** {summary.medium_conflicts}")
        lines.append(f"  - **Semantic Overlaps & Duplicates:** {summary.semantic_overlaps + summary.duplicates}")
        lines.append("\n---\n")
        lines.append("## Detailed Conflict Log\n")

        for idx, c in enumerate(conflicts, 1):
            lines.append(f"### {idx}. [{c.conflict_id}] {c.conflict_type} ({c.severity} Severity)")
            lines.append(f"- **Similarity / Alignment Score:** {int(c.similarity_score * 100)}%\n")
            lines.append(f"| Attribute | Requirement 1 | Requirement 2 |")
            lines.append(f"| :--- | :--- | :--- |")
            lines.append(f"| **Reference** | `{c.requirement_1.reference_code}` | `{c.requirement_2.reference_code}` |")
            lines.append(f"| **Document** | {c.requirement_1.source_document} | {c.requirement_2.source_document} |")
            lines.append(f"| **Section** | {c.requirement_1.section} | {c.requirement_2.section} |")
            lines.append(f"| **Page** | {c.requirement_1.page_number or 'N/A'} | {c.requirement_2.page_number or 'N/A'} |")
            lines.append(f"| **Text** | \"{c.requirement_1.requirement_text}\" | \"{c.requirement_2.requirement_text}\" |")
            lines.append(f"\n**Conflicting Elements:** {c.conflicting_elements}")
            lines.append(f"\n**Semantic Explanation:**\n> {c.explanation}")
            lines.append(f"\n**Suggested Clarification:**\n> {c.suggested_clarification}\n")
            lines.append("---\n")

        return "\n".join(lines)
