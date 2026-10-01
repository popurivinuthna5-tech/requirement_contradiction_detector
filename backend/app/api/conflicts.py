from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Response, status
from app.models.schemas import ConflictResponse, ConflictSummary, AnalysisRunRequest, UserProfile
from app.services.auth_service import get_current_user
from app.services.conflict_analyzer import ConflictAnalyzerService
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/conflicts", tags=["Conflicts"])

@router.post("/analyze")
async def trigger_analysis(
    payload: AnalysisRunRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """Executes semantic comparison and conflict analysis across requirements."""
    result = ConflictAnalyzerService.run_analysis(
        user_id=current_user.user_id,
        document_ids=payload.document_ids,
        similarity_threshold=payload.similarity_threshold or 0.40,
        provider_name=payload.ai_provider
    )
    return result

@router.get("", response_model=List[ConflictResponse])
async def list_conflicts(
    severity: Optional[str] = Query(None),
    conflict_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    document_id: Optional[str] = Query(None),
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieves list of conflicts with filters for search, severity, type, and source document."""
    return ConflictAnalyzerService.get_conflicts_list(
        user_id=current_user.user_id,
        severity=severity,
        conflict_type=conflict_type,
        search_query=search,
        document_id=document_id
    )

@router.get("/summary", response_model=ConflictSummary)
async def get_summary(current_user: UserProfile = Depends(get_current_user)):
    """Computes real-time metrics and breakdown statistics for dashboard visualizations."""
    return ConflictAnalyzerService.get_summary(user_id=current_user.user_id)

@router.get("/{conflict_id}", response_model=ConflictResponse)
async def get_conflict_detail(
    conflict_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Retrieves detailed side-by-side comparison data for an individual conflict."""
    conflicts = ConflictAnalyzerService.get_conflicts_list(user_id=current_user.user_id)
    for c in conflicts:
        if c.conflict_id == conflict_id:
            return c
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conflict record not found.")

@router.get("/export/{export_format}")
async def export_report(
    export_format: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Exports the conflict and overlap analysis report in CSV, JSON, or Markdown."""
    summary = ConflictAnalyzerService.get_summary(user_id=current_user.user_id)
    conflicts = ConflictAnalyzerService.get_conflicts_list(user_id=current_user.user_id)
    
    fmt = export_format.lower()
    if fmt == "csv":
        csv_data = ReportService.generate_csv(conflicts)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=requirement_conflicts_report.csv"}
        )
    elif fmt == "json":
        json_data = ReportService.generate_json(summary, conflicts)
        return Response(
            content=json_data,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=requirement_conflicts_report.json"}
        )
    elif fmt in ["md", "markdown"]:
        md_data = ReportService.generate_markdown(summary, conflicts)
        return Response(
            content=md_data,
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=requirement_conflicts_report.md"}
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Supported export formats: csv, json, md")
