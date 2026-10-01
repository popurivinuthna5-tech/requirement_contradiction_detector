from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ConflictAnalysisResult(BaseModel):
    is_conflict_or_overlap: bool
    conflict_type: str # Direct Contradiction | Partial Conflict | Semantic Overlap | Duplicate | Ambiguity | Potential Conflict
    severity: str # Critical | High | Medium | Low
    similarity_score: float
    conflicting_elements: str
    explanation: str
    suggested_clarification: str

class BaseAIProvider(ABC):
    """Abstract base class for semantic requirement conflict analysis providers."""
    
    @abstractmethod
    def analyze_requirement_pair(
        self,
        req1_text: str,
        req1_ref: str,
        req2_text: str,
        req2_ref: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ConflictAnalysisResult]:
        """
        Analyzes a pair of requirements for semantic relationship, contradictions,
        overlaps, duplicates, and ambiguities.
        Returns ConflictAnalysisResult if a notable relationship/conflict exists, or None if unrelated or non-conflicting.
        """
        pass
    
    @abstractmethod
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Returns semantic similarity score between 0.0 and 1.0."""
        pass
