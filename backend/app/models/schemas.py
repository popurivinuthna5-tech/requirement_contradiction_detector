from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# User Schemas
class UserProfile(BaseModel):
    user_id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    provider: str = "google"
    created_at: Optional[str] = None

class AuthVerifyRequest(BaseModel):
    id_token: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    display_name: Optional[str] = None
    provider: Optional[str] = "google"

# Document Schemas
class DocumentResponse(BaseModel):
    document_id: str
    user_id: str
    filename: str
    original_filename: str
    document_type: str
    file_size: int
    upload_date: str
    status: str
    requirement_count: int
    error_message: Optional[str] = None

# Requirement Schemas
class RequirementResponse(BaseModel):
    requirement_id: str
    document_id: str
    user_id: str
    reference_code: str
    requirement_text: str
    requirement_type: str
    section: Optional[str] = "General"
    page_number: Optional[int] = None
    priority: Optional[str] = "Unspecified"
    metadata_json: Optional[Dict[str, Any]] = None
    document_name: Optional[str] = None
    created_at: Optional[str] = None

# Traceable Requirement for side-by-side comparison
class TraceableRequirement(BaseModel):
    requirement_id: str
    reference_code: str
    requirement_text: str
    requirement_type: str
    source_document: str
    document_id: str
    section: str
    page_number: Optional[int] = None
    priority: str

# Conflict Schemas
class ConflictResponse(BaseModel):
    conflict_id: str
    conflict_type: str # Direct Contradiction | Partial Conflict | Semantic Overlap | Duplicate | Ambiguity | Potential Conflict
    severity: str # Critical | High | Medium | Low
    similarity_score: float
    explanation: str
    conflicting_elements: Optional[str] = None
    suggested_clarification: Optional[str] = None
    created_at: Optional[str] = None
    requirement_1: TraceableRequirement
    requirement_2: TraceableRequirement

class ConflictSummary(BaseModel):
    total_documents: int = 0
    total_requirements: int = 0
    total_relationships: int = 0
    total_conflicts: int = 0
    critical_conflicts: int = 0
    high_conflicts: int = 0
    medium_conflicts: int = 0
    low_conflicts: int = 0
    direct_contradictions: int = 0
    partial_conflicts: int = 0
    semantic_overlaps: int = 0
    duplicates: int = 0
    ambiguities: int = 0
    conflicts_by_document: Dict[str, int] = {}
    severity_distribution: Dict[str, int] = {}
    type_distribution: Dict[str, int] = {}

class AnalysisRunRequest(BaseModel):
    document_ids: Optional[List[str]] = None
    similarity_threshold: Optional[float] = 0.55
    ai_provider: Optional[str] = None

class ProviderSettings(BaseModel):
    active_provider: str
    available_providers: List[str]
    openai_configured: bool
    gemini_configured: bool
    claude_configured: bool
    ollama_url: str
