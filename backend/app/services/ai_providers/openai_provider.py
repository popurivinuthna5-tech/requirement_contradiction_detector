import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.services.ai_providers.base import BaseAIProvider, ConflictAnalysisResult
from app.services.ai_providers.smart_local import SmartLocalProvider
from app.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Systems Requirements Engineering AI.
Your task is to analyze two software requirements extracted from specification documents (e.g. SRS, BRD, PRD) and determine their semantic relationship.

CRITICAL RULES:
1. Do NOT report every semantically similar requirement as a conflict! If two requirements are merely related or address adjacent features of the same domain, classify as 'Semantic Overlap' with Low severity, NOT a conflict.
2. Only classify as 'Direct Contradiction' or 'Partial Conflict' when requirements contain genuinely incompatible or conflicting conditions, rules, numerical thresholds, timing, roles, permissions, or workflows.
3. Categorize into one of:
   - 'Direct Contradiction'
   - 'Partial Conflict'
   - 'Semantic Overlap'
   - 'Duplicate'
   - 'Ambiguity'
   - 'None' (if completely compatible and unrelated)
4. Severity: 'Critical' | 'High' | 'Medium' | 'Low'.
5. Always output STRICT VALID JSON matching this schema:
{
  "is_conflict_or_overlap": boolean,
  "conflict_type": string,
  "severity": string,
  "similarity_score": float (0.0 to 1.0),
  "conflicting_elements": string,
  "explanation": string,
  "suggested_clarification": string
}
If there is no conflict, duplicate, ambiguity, or overlap, return "is_conflict_or_overlap": false.
"""

class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_MODEL
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.fallback = SmartLocalProvider()

    def calculate_similarity(self, text1: str, text2: str) -> float:
        return self.fallback.calculate_similarity(text1, text2)

    def analyze_requirement_pair(
        self,
        req1_text: str,
        req1_ref: str,
        req2_text: str,
        req2_ref: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ConflictAnalysisResult]:
        if not self.client:
            return self.fallback.analyze_requirement_pair(req1_text, req1_ref, req2_text, req2_ref, context)

        user_content = f"""Requirement 1 ({req1_ref}):
"{req1_text}"

Requirement 2 ({req2_ref}):
"{req2_text}"

Analyze their relationship, detecting any direct contradiction, partial conflict, semantic overlap, duplicate, or ambiguity.
Return the structured JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            raw = response.choices[0].message.content
            data = json.loads(raw)
            
            if not data.get("is_conflict_or_overlap", False):
                return None
                
            return ConflictAnalysisResult(
                is_conflict_or_overlap=True,
                conflict_type=data.get("conflict_type", "Partial Conflict"),
                severity=data.get("severity", "Medium"),
                similarity_score=float(data.get("similarity_score", 0.75)),
                conflicting_elements=data.get("conflicting_elements", "Differing conditions"),
                explanation=data.get("explanation", ""),
                suggested_clarification=data.get("suggested_clarification", "")
            )
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}. Falling back to SmartLocalProvider.")
            return self.fallback.analyze_requirement_pair(req1_text, req1_ref, req2_text, req2_ref, context)
