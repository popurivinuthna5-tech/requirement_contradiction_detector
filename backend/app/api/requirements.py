import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from app.database import get_db
from app.models.schemas import RequirementResponse, UserProfile
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/requirements", tags=["Requirements"])

@router.get("", response_model=List[RequirementResponse])
async def list_requirements(
    document_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    req_type: Optional[str] = Query(None),
    current_user: UserProfile = Depends(get_current_user)
):
    """Lists requirements with optional search, document, and type filtering."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT r.*, d.original_filename as document_name
            FROM requirements r
            JOIN documents d ON r.document_id = d.document_id
            WHERE r.user_id = ?
        """
        params = [current_user.user_id]

        if document_id and document_id.lower() != "all":
            query += " AND r.document_id = ?"
            params.append(document_id)

        if req_type and req_type.lower() != "all":
            query += " AND r.requirement_type = ?"
            params.append(req_type)

        if search:
            query += " AND (r.requirement_text LIKE ? OR r.reference_code LIKE ? OR r.section LIKE ?)"
            wildcard = f"%{search}%"
            params.extend([wildcard, wildcard, wildcard])

        query += " ORDER BY r.reference_code ASC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            meta = {}
            if row["metadata_json"]:
                try:
                    meta = json.loads(row["metadata_json"])
                except Exception:
                    pass
            results.append(RequirementResponse(
                requirement_id=row["requirement_id"],
                document_id=row["document_id"],
                user_id=row["user_id"],
                reference_code=row["reference_code"],
                requirement_text=row["requirement_text"],
                requirement_type=row["requirement_type"],
                section=row["section"] or "General",
                page_number=row["page_number"],
                priority=row["priority"] or "Medium",
                metadata_json=meta,
                document_name=row["document_name"],
                created_at=row["created_at"]
            ))
        return results

@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement_detail(
    requirement_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieves full detail of an individual requirement."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, d.original_filename as document_name
            FROM requirements r
            JOIN documents d ON r.document_id = d.document_id
            WHERE r.requirement_id = ? AND r.user_id = ?
        """, (requirement_id, current_user.user_id))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found.")
        
        meta = {}
        if row["metadata_json"]:
            try:
                meta = json.loads(row["metadata_json"])
            except Exception:
                pass
        return RequirementResponse(
            requirement_id=row["requirement_id"],
            document_id=row["document_id"],
            user_id=row["user_id"],
            reference_code=row["reference_code"],
            requirement_text=row["requirement_text"],
            requirement_type=row["requirement_type"],
            section=row["section"] or "General",
            page_number=row["page_number"],
            priority=row["priority"] or "Medium",
            metadata_json=meta,
            document_name=row["document_name"],
            created_at=row["created_at"]
        )
