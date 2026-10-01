import os
import uuid
import shutil
import json
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES
from app.database import get_db
from app.models.schemas import DocumentResponse, UserProfile
from app.services.auth_service import get_current_user
from app.services.document_parser import DocumentParser
from app.services.requirement_extractor import RequirementExtractor

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserProfile = Depends(get_current_user)
):
    """Uploads, validates, parses, and extracts structured requirements from a document."""
    original_filename = file.filename or "requirement_document.txt"
    ext = Path(original_filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read content to check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES / (1024 * 1024):.0f} MB."
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty. Please provide a valid requirement document."
        )

    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    user_upload_dir = UPLOAD_DIR / current_user.user_id
    user_upload_dir.mkdir(parents=True, exist_ok=True)
    saved_filename = f"{doc_id}_{original_filename}"
    file_path = user_upload_dir / saved_filename

    # Save to disk
    with open(file_path, "wb") as f:
        f.write(contents)

    # Save initial record in DB with status 'extracting'
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO documents (
                document_id, user_id, filename, original_filename,
                document_type, file_path, file_size, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'extracting')
        """, (
            doc_id, current_user.user_id, saved_filename, original_filename,
            ext, str(file_path), len(contents)
        ))
        conn.commit()

    # Parse and extract
    try:
        blocks = DocumentParser.parse_file(file_path, ext)
        extracted = RequirementExtractor.extract_from_blocks(blocks, original_filename)

        with get_db() as conn:
            cursor = conn.cursor()
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
            
            cursor.execute("""
                UPDATE documents 
                SET status = 'uploaded', requirement_count = ?
                WHERE document_id = ?
            """, (len(extracted), doc_id))
            conn.commit()

    except Exception as err:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents 
                SET status = 'failed', error_message = ?
                WHERE document_id = ?
            """, (str(err), doc_id))
            conn.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract requirements from {original_filename}: {str(err)}"
        )

    # Return created document record
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE document_id = ?", (doc_id,))
        row = cursor.fetchone()
        return DocumentResponse(**dict(row))

@router.get("", response_model=List[DocumentResponse])
async def list_documents(current_user: UserProfile = Depends(get_current_user)):
    """Lists all documents belonging to the authenticated user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE user_id = ? ORDER BY upload_date DESC", (current_user.user_id,))
        rows = cursor.fetchall()
        return [DocumentResponse(**dict(row)) for row in rows]

@router.delete("/{document_id}")
async def delete_document(document_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Deletes a document and its requirements/conflicts."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM documents WHERE document_id = ? AND user_id = ?", (document_id, current_user.user_id))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        file_path = row["file_path"]
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        # Foreign keys with CASCADE will delete requirements and conflicts
        cursor.execute("DELETE FROM documents WHERE document_id = ? AND user_id = ?", (document_id, current_user.user_id))
        conn.commit()

    return {"message": "Document and associated requirements deleted successfully."}
