import json
import logging
import requests
from typing import Dict, Any, Optional
from app.services.ai_providers.base import BaseAIProvider, ConflictAnalysisResult
from app.services.ai_providers.smart_local import SmartLocalProvider
from app.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

GEMINI_SYSTEM_INSTRUCTION = """You are an expert Systems Requirements Engineering AI.
Analyze two software requirements for contradictions, partial conflicts, semantic overlaps, duplicates, or ambiguities.
Distinguish semantic similarity from true logical contradictions.
Return strictly valid JSON with keys:
"is_conflict_or_overlap": bool, "conflict_type": str, "severity": str, "similarity_score": float, "conflicting_elements": str, "explanation": str, "suggested_clarification": str.
"""

class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or GEMINI_MODEL
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
        if not self.api_key:
            return self.fallback.analyze_requirement_pair(req1_text, req1_ref, req2_text, req2_ref, context)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        prompt = f"""{GEMINI_SYSTEM_INSTRUCTION}

Requirement 1 [{req1_ref}]: "{req1_text}"
Requirement 2 [{req2_ref}]: "{req2_text}"
"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        }

        try:
            res = requests.post(url, json=payload, timeout=15)
            if res.status_code == 200:
                data = res.json()
                text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text_content)
                if not parsed.get("is_conflict_or_overlap", False):
                    return None
                return ConflictAnalysisResult(
                    is_conflict_or_overlap=True,
                    conflict_type=parsed.get("conflict_type", "Partial Conflict"),
                    severity=parsed.get("severity", "Medium"),
                    similarity_score=float(parsed.get("similarity_score", 0.75)),
                    conflicting_elements=parsed.get("conflicting_elements", "Differing conditions"),
                    explanation=parsed.get("explanation", ""),
                    suggested_clarification=parsed.get("suggested_clarification", "")
                )
            else:
                logger.warning(f"Gemini API returned status {res.status_code}. Using local engine fallback.")
        except Exception as e:
            logger.warning(f"Gemini call exception: {e}. Falling back to SmartLocalProvider.")

        return self.fallback.analyze_requirement_pair(req1_text, req1_ref, req2_text, req2_ref, context)
