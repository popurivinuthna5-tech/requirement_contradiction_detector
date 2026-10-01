import shutil
from pathlib import Path
from fastapi import APIRouter, Depends
from app.config import BASE_DIR, UPLOAD_DIR
from app.database import get_db
from app.models.schemas import UserProfile
from app.services.auth_service import get_current_user
from app.services.document_parser import DocumentParser
from app.services.requirement_extractor import RequirementExtractor
from app.services.conflict_analyzer import ConflictAnalyzerService
import json

router = APIRouter(prefix="/api/demo", tags=["Demo"])

@router.post("/load")
async def load_demo_data(current_user: UserProfile = Depends(get_current_user)):
    """
    Populates the authenticated user's workspace with sample SRS and BRD requirement documents
    and triggers instant semantic conflict & overlap analysis.
    """
    sample_dir = BASE_DIR / "sample_data"
    srs_file = sample_dir / "E-Commerce_Platform_SRS.txt"
    brd_file = sample_dir / "E-Commerce_Business_Requirements_BRD.txt"

    user_upload_dir = UPLOAD_DIR / current_user.user_id
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    created_doc_ids = []

    for sample_path, doc_label, filename in [
        (srs_file, "SRS", "E-Commerce_Platform_SRS.txt"),
        (brd_file, "BRD", "E-Commerce_Business_Requirements_BRD.txt")
    ]:
        doc_id = f"demo_{doc_label.lower()}_{current_user.user_id[:6]}"
        target_path = user_upload_dir / f"{doc_id}_{filename}"
        shutil.copyfile(sample_path, target_path)

        # Parse & extract
        blocks = DocumentParser.parse_txt(target_path)
        extracted = RequirementExtractor.extract_from_blocks(blocks, filename)

        with get_db() as conn:
            cursor = conn.cursor()
            # Upsert document
            cursor.execute("""
                INSERT OR REPLACE INTO documents (
                    document_id, user_id, filename, original_filename,
                    document_type, file_path, file_size, status, requirement_count
                ) VALUES (?, ?, ?, ?, '.txt', ?, ?, 'uploaded', ?)
            """, (
                doc_id, current_user.user_id, f"{doc_id}_{filename}", filename,
                str(target_path), target_path.stat().st_size, len(extracted)
            ))
            
            # Delete old requirements for this doc if reloading
            cursor.execute("DELETE FROM requirements WHERE document_id = ?", (doc_id,))
            
            for req in extracted:
                cursor.execute("""
                    INSERT INTO requirements (
                        requirement_id, document_id, user_id, reference_code,
                        requirement_text, requirement_type, section, page_number,
                        priority, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    req.requirement_id, doc_id, current_user.user_id, req.reference_code,
                    req.requirement_text, req.requirement_type, req.section, req.page_number,
                    req.priority, json.dumps(req.metadata)
                ))
            conn.commit()

        created_doc_ids.append(doc_id)

    # Run analysis automatically
    analysis_res = ConflictAnalyzerService.run_analysis(
        user_id=current_user.user_id,
        document_ids=created_doc_ids,
        similarity_threshold=0.40
    )

    summary = ConflictAnalyzerService.get_summary(user_id=current_user.user_id)

    return {
        "message": "Demo requirement documents and semantic conflict analysis successfully loaded.",
        "documents_loaded": len(created_doc_ids),
        "document_ids": created_doc_ids,
        "summary": summary
    }
