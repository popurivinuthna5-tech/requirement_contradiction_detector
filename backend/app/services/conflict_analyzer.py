import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.database import get_db
from app.services.ai_providers.provider_factory import AIProviderFactory
from app.models.schemas import ConflictSummary, ConflictResponse, TraceableRequirement

logger = logging.getLogger(__name__)

class ConflictAnalyzerService:
    """Orchestrates pairwise semantic comparison, contradiction detection, and report generation."""

    @classmethod
    def run_analysis(
        cls,
        user_id: str,
        document_ids: Optional[List[str]] = None,
        similarity_threshold: float = 0.40,
        provider_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes semantic analysis across requirements for the given user and documents.
        """
        provider = AIProviderFactory.get_provider(provider_name)
        
        # 1. Fetch requirements
        requirements = cls._fetch_requirements(user_id, document_ids)
        if len(requirements) < 2:
            return {
                "message": "At least two requirements are needed to perform conflict analysis.",
                "total_analyzed": len(requirements),
                "conflicts_found": 0
            }

        # 2. Clear existing conflicts for these requirements/documents to prevent duplicates
        cls._clear_prior_conflicts(user_id, document_ids)

        conflicts_created = []
        total_pairs_evaluated = 0

        # 3. Pairwise analysis
        for i in range(len(requirements)):
            req1 = requirements[i]
            for j in range(i + 1, len(requirements)):
                req2 = requirements[j]
                total_pairs_evaluated += 1

                # Quick pre-filter: check if there's any semantic similarity or domain relation
                quick_sim = provider.calculate_similarity(req1["requirement_text"], req2["requirement_text"])
                
                # If similarity is above minimum threshold or contains critical security/timing/auth keywords
                needs_deep_check = quick_sim >= similarity_threshold or cls._has_common_sensitive_domain(req1["requirement_text"], req2["requirement_text"])

                if needs_deep_check:
                    try:
                        result = provider.analyze_requirement_pair(
                            req1_text=req1["requirement_text"],
                            req1_ref=req1["reference_code"],
                            req2_text=req2["requirement_text"],
                            req2_ref=req2["reference_code"],
                            context={"doc1": req1["doc_name"], "doc2": req2["doc_name"]}
                        )
                        
                        if result and result.is_conflict_or_overlap:
                            conflict_id = f"conf_{uuid.uuid4().hex[:12]}"
                            cls._save_conflict(
                                conflict_id=conflict_id,
                                user_id=user_id,
                                req1_id=req1["requirement_id"],
                                req2_id=req2["requirement_id"],
                                conflict_type=result.conflict_type,
                                severity=result.severity,
                                similarity_score=result.similarity_score,
                                explanation=result.explanation,
                                conflicting_elements=result.conflicting_elements,
                                suggested_clarification=result.suggested_clarification
                            )
                            conflicts_created.append(conflict_id)
                    except Exception as err:
                        logger.error(f"Error evaluating pair {req1['reference_code']} and {req2['reference_code']}: {err}")

        # Update document status to 'completed'
        cls._mark_documents_analyzed(user_id, document_ids)

        return {
            "status": "completed",
            "total_requirements": len(requirements),
            "pairs_evaluated": total_pairs_evaluated,
            "conflicts_found": len(conflicts_created),
            "conflict_ids": conflicts_created
        }

    @classmethod
    def get_summary(cls, user_id: str) -> ConflictSummary:
        """Computes executive metrics for dashboard cards and charts."""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Total documents
            cursor.execute("SELECT COUNT(*) as count FROM documents WHERE user_id = ?", (user_id,))
            total_docs = cursor.fetchone()["count"]
            
            # Total requirements
            cursor.execute("SELECT COUNT(*) as count FROM requirements WHERE user_id = ?", (user_id,))
            total_reqs = cursor.fetchone()["count"]
            
            # Total conflicts
            cursor.execute("SELECT COUNT(*) as count FROM conflicts WHERE user_id = ?", (user_id,))
            total_conflicts = cursor.fetchone()["count"]
            
            # By severity
            cursor.execute("""
                SELECT severity, COUNT(*) as count 
                FROM conflicts 
                WHERE user_id = ? 
                GROUP BY severity
            """, (user_id,))
            sev_rows = cursor.fetchall()
            sev_dict = {row["severity"]: row["count"] for row in sev_rows}
            
            # By conflict type
            cursor.execute("""
                SELECT conflict_type, COUNT(*) as count 
                FROM conflicts 
                WHERE user_id = ? 
                GROUP BY conflict_type
            """, (user_id,))
            type_rows = cursor.fetchall()
            type_dict = {row["conflict_type"]: row["count"] for row in type_rows}

            # Conflicts by document
            cursor.execute("""
                SELECT d.original_filename, COUNT(c.conflict_id) as count
                FROM conflicts c
                JOIN requirements r ON c.requirement_1_id = r.requirement_id
                JOIN documents d ON r.document_id = d.document_id
                WHERE c.user_id = ?
                GROUP BY d.original_filename
            """, (user_id,))
            doc_rows = cursor.fetchall()
            doc_dict = {row["original_filename"]: row["count"] for row in doc_rows}

            return ConflictSummary(
                total_documents=total_docs,
                total_requirements=total_reqs,
                total_relationships=total_conflicts,
                total_conflicts=sev_dict.get("Critical", 0) + sev_dict.get("High", 0) + sev_dict.get("Medium", 0),
                critical_conflicts=sev_dict.get("Critical", 0),
                high_conflicts=sev_dict.get("High", 0),
                medium_conflicts=sev_dict.get("Medium", 0),
                low_conflicts=sev_dict.get("Low", 0),
                direct_contradictions=type_dict.get("Direct Contradiction", 0),
                partial_conflicts=type_dict.get("Partial Conflict", 0),
                semantic_overlaps=type_dict.get("Semantic Overlap", 0),
                duplicates=type_dict.get("Duplicate", 0),
                ambiguities=type_dict.get("Ambiguity", 0),
                conflicts_by_document=doc_dict,
                severity_distribution=sev_dict,
                type_distribution=type_dict
            )

    @classmethod
    def get_conflicts_list(
        cls,
        user_id: str,
        severity: Optional[str] = None,
        conflict_type: Optional[str] = None,
        search_query: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> List[ConflictResponse]:
        """Fetches detailed traceable conflicts list with side-by-side requirement metadata."""
        with get_db() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    c.conflict_id, c.conflict_type, c.severity, c.similarity_score,
                    c.explanation, c.conflicting_elements, c.suggested_clarification, c.created_at,
                    r1.requirement_id as r1_id, r1.reference_code as r1_ref, r1.requirement_text as r1_text,
                    r1.requirement_type as r1_type, r1.section as r1_sec, r1.page_number as r1_page,
                    r1.priority as r1_prio, r1.document_id as r1_doc_id, d1.original_filename as r1_doc_name,
                    r2.requirement_id as r2_id, r2.reference_code as r2_ref, r2.requirement_text as r2_text,
                    r2.requirement_type as r2_type, r2.section as r2_sec, r2.page_number as r2_page,
                    r2.priority as r2_prio, r2.document_id as r2_doc_id, d2.original_filename as r2_doc_name
                FROM conflicts c
                JOIN requirements r1 ON c.requirement_1_id = r1.requirement_id
                JOIN requirements r2 ON c.requirement_2_id = r2.requirement_id
                JOIN documents d1 ON r1.document_id = d1.document_id
                JOIN documents d2 ON r2.document_id = d2.document_id
                WHERE c.user_id = ?
            """
            params: List[Any] = [user_id]

            if severity and severity.lower() != "all":
                query += " AND c.severity = ?"
                params.append(severity)

            if conflict_type and conflict_type.lower() != "all":
                query += " AND c.conflict_type = ?"
                params.append(conflict_type)

            if document_id and document_id.lower() != "all":
                query += " AND (r1.document_id = ? OR r2.document_id = ?)"
                params.extend([document_id, document_id])

            if search_query:
                query += " AND (r1.requirement_text LIKE ? OR r2.requirement_text LIKE ? OR c.explanation LIKE ? OR r1.reference_code LIKE ? OR r2.reference_code LIKE ?)"
                wildcard = f"%{search_query}%"
                params.extend([wildcard, wildcard, wildcard, wildcard, wildcard])

            query += " ORDER BY CASE c.severity WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END, c.created_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results: List[ConflictResponse] = []
            for row in rows:
                req1 = TraceableRequirement(
                    requirement_id=row["r1_id"],
                    reference_code=row["r1_ref"],
                    requirement_text=row["r1_text"],
                    requirement_type=row["r1_type"],
                    source_document=row["r1_doc_name"],
                    document_id=row["r1_doc_id"],
                    section=row["r1_sec"] or "General",
                    page_number=row["r1_page"],
                    priority=row["r1_prio"] or "Medium"
                )
                req2 = TraceableRequirement(
                    requirement_id=row["r2_id"],
                    reference_code=row["r2_ref"],
                    requirement_text=row["r2_text"],
                    requirement_type=row["r2_type"],
                    source_document=row["r2_doc_name"],
                    document_id=row["r2_doc_id"],
                    section=row["r2_sec"] or "General",
                    page_number=row["r2_page"],
                    priority=row["r2_prio"] or "Medium"
                )
                results.append(ConflictResponse(
                    conflict_id=row["conflict_id"],
                    conflict_type=row["conflict_type"],
                    severity=row["severity"],
                    similarity_score=float(row["similarity_score"]),
                    explanation=row["explanation"],
                    conflicting_elements=row["conflicting_elements"],
                    suggested_clarification=row["suggested_clarification"],
                    created_at=row["created_at"],
                    requirement_1=req1,
                    requirement_2=req2
                ))
            return results

    @classmethod
    def _fetch_requirements(cls, user_id: str, document_ids: Optional[List[str]]) -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            if document_ids:
                placeholders = ",".join("?" for _ in document_ids)
                cursor.execute(f"""
                    SELECT r.requirement_id, r.reference_code, r.requirement_text, r.requirement_type,
                           r.section, r.page_number, r.priority, r.document_id, d.original_filename as doc_name
                    FROM requirements r
                    JOIN documents d ON r.document_id = d.document_id
                    WHERE r.user_id = ? AND r.document_id IN ({placeholders})
                """, [user_id] + document_ids)
            else:
                cursor.execute("""
                    SELECT r.requirement_id, r.reference_code, r.requirement_text, r.requirement_type,
                           r.section, r.page_number, r.priority, r.document_id, d.original_filename as doc_name
                    FROM requirements r
                    JOIN documents d ON r.document_id = d.document_id
                    WHERE r.user_id = ?
                """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    @classmethod
    def _save_conflict(
        cls, conflict_id: str, user_id: str, req1_id: str, req2_id: str,
        conflict_type: str, severity: str, similarity_score: float,
        explanation: str, conflicting_elements: str, suggested_clarification: str
    ):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conflicts (
                    conflict_id, user_id, requirement_1_id, requirement_2_id,
                    conflict_type, severity, similarity_score, explanation,
                    conflicting_elements, suggested_clarification
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conflict_id, user_id, req1_id, req2_id,
                conflict_type, severity, similarity_score, explanation,
                conflicting_elements, suggested_clarification
            ))
            conn.commit()

    @classmethod
    def _clear_prior_conflicts(cls, user_id: str, document_ids: Optional[List[str]]):
        with get_db() as conn:
            cursor = conn.cursor()
            if document_ids:
                placeholders = ",".join("?" for _ in document_ids)
                cursor.execute(f"""
                    DELETE FROM conflicts WHERE user_id = ? AND (
                        requirement_1_id IN (SELECT requirement_id FROM requirements WHERE document_id IN ({placeholders}))
                        OR requirement_2_id IN (SELECT requirement_id FROM requirements WHERE document_id IN ({placeholders}))
                    )
                """, [user_id] + document_ids + document_ids)
            else:
                cursor.execute("DELETE FROM conflicts WHERE user_id = ?", (user_id,))
            conn.commit()

    @classmethod
    def _mark_documents_analyzed(cls, user_id: str, document_ids: Optional[List[str]]):
        with get_db() as conn:
            cursor = conn.cursor()
            if document_ids:
                placeholders = ",".join("?" for _ in document_ids)
                cursor.execute(f"UPDATE documents SET status = 'completed' WHERE user_id = ? AND document_id IN ({placeholders})", [user_id] + document_ids)
            else:
                cursor.execute("UPDATE documents SET status = 'completed' WHERE user_id = ?", (user_id,))
            conn.commit()

    @staticmethod
    def _has_common_sensitive_domain(t1: str, t2: str) -> bool:
        sensitive = ["password", "reset", "session", "inactivity", "cancel", "shipment", "refund", "auth", "2fa", "admin", "export", "lockout"]
        t1_low, t2_low = t1.lower(), t2.lower()
        return any(s in t1_low and s in t2_low for s in sensitive)
