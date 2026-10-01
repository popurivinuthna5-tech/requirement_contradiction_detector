import re
import uuid
from typing import List, Dict, Any, Optional
from app.services.document_parser import DocumentBlock

class ExtractedRequirement:
    def __init__(
        self,
        reference_code: str,
        requirement_text: str,
        requirement_type: str,
        section: str,
        page_number: Optional[int],
        priority: str,
        metadata: Dict[str, Any]
    ):
        self.requirement_id = f"req_{uuid.uuid4().hex[:12]}"
        self.reference_code = reference_code
        self.requirement_text = requirement_text.strip()
        self.requirement_type = requirement_type
        self.section = section or "General"
        self.page_number = page_number
        self.priority = priority
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "reference_code": self.reference_code,
            "requirement_text": self.requirement_text,
            "requirement_type": self.requirement_type,
            "section": self.section,
            "page_number": self.page_number,
            "priority": self.priority,
            "metadata_json": self.metadata
        }

class RequirementExtractor:
    """Extracts atomic, structured requirements from document blocks and generates traceable IDs."""

    @classmethod
    def extract_from_blocks(cls, blocks: List[DocumentBlock], document_filename: str) -> List[ExtractedRequirement]:
        requirements: List[ExtractedRequirement] = []
        prefix = cls._derive_document_prefix(document_filename)
        counter = 1

        for block in blocks:
            text = block.text.strip()
            if not text or len(text) < 15:
                continue
                
            # Skip boilerplate metadata
            if cls._is_boilerplate(text):
                continue

            # Split block into candidate sentences/clauses
            candidates = cls._split_into_requirement_units(text)
            
            for candidate in candidates:
                cand_clean = candidate.strip()
                if not cand_clean or len(cand_clean) < 18:
                    continue
                
                # Check if this statement expresses a requirement or business rule
                if not cls._is_requirement_statement(cand_clean):
                    # If it's part of a structured requirements section, keep it if it's descriptive
                    if not any(k in block.section.lower() for k in ["requirement", "specification", "scope", "function", "security", "rule"]):
                        continue

                # Check if text already has a tag like [REQ-001] or RQ-BRD-014 or SRS-002:
                existing_tag = cls._find_existing_reference(cand_clean)
                if existing_tag:
                    ref_code = existing_tag
                    # Clean the tag off the beginning if desired, but keep original intent
                    clean_text = re.sub(r'^(?:\[[^\]]+\]|\b(?:REQ|RQ|SRS|BRD|FRD|FR|BR)-\d+\b[:\s\-]*)', '', cand_clean).strip()
                    if not clean_text:
                        clean_text = cand_clean
                else:
                    ref_code = f"{prefix}-{counter:03d}"
                    clean_text = cand_clean
                    counter += 1

                req_type = cls._classify_requirement_type(clean_text, block.section)
                priority = cls._determine_priority(clean_text)
                entities = cls._extract_entities(clean_text)

                req = ExtractedRequirement(
                    reference_code=ref_code,
                    requirement_text=clean_text,
                    requirement_type=req_type,
                    section=block.section,
                    page_number=block.page_number,
                    priority=priority,
                    metadata={"entities": entities, "original_clause": cand_clean}
                )
                requirements.append(req)

        return requirements

    @staticmethod
    def _derive_document_prefix(filename: str) -> str:
        name_upper = filename.upper()
        if "SRS" in name_upper:
            return "SRS"
        elif "BRD" in name_upper:
            return "BRD"
        elif "PRD" in name_upper:
            return "PRD"
        elif "FRD" in name_upper or "FUNCTIONAL" in name_upper:
            return "FRD"
        elif "NFR" in name_upper:
            return "NFR"
        else:
            # Extract clean letters
            clean = re.sub(r'[^A-Z]', '', name_upper[:5])
            return clean if len(clean) >= 2 else "REQ"

    @staticmethod
    def _find_existing_reference(text: str) -> Optional[str]:
        match = re.search(r'\b(RQ-[A-Z]+-\d+|[A-Z]{2,4}-\d{2,4}|REQ-\d+|FR-\d+|BR-\d+)\b', text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        match_bracket = re.search(r'\[([A-Z0-9_\-]+)\]', text)
        if match_bracket:
            val = match_bracket.group(1)
            if any(char.isdigit() for char in val):
                return val.upper()
        return None

    @staticmethod
    def _is_requirement_statement(text: str) -> bool:
        """Determines if the text contains modal verbs, imperative verbs, or constraint syntax."""
        text_lower = text.lower()
        keywords = [
            "must", "shall", "should", "will", "required", "needs to", "ought to",
            "can", "may", "allows", "enables", "prohibits", "restricted to", "cannot",
            "shall not", "must not", "only", "responsible for", "expected to",
            "minimum", "maximum", "at least", "no more than", "within", "timeout",
            "cancel", "reset", "authenticate", "authorize", "validate", "log", "retain"
        ]
        return any(k in text_lower for k in keywords)

    @staticmethod
    def _is_boilerplate(text: str) -> bool:
        t_low = text.lower()
        boilerplates = [
            "table of contents", "confidential", "all rights reserved",
            "page 1 of", "document version", "author:", "approved by:",
            "distribution list", "revision history"
        ]
        return any(b in t_low for b in boilerplates) and len(text) < 120

    @classmethod
    def _split_into_requirement_units(cls, text: str) -> List[str]:
        # If text has bullet points or numbered lists: 1. ... 2. ... or - ... * ...
        if re.search(r'(?:^\s*[-*•]|\n\s*[-*•]|\d+\.\s+[A-Z])', text):
            lines = re.split(r'\n(?=\s*(?:[-*•]|\d+\.))', text)
            result = []
            for l in lines:
                cleaned = re.sub(r'^\s*[-*•\d\.]+\s*', '', l).strip()
                if cleaned:
                    result.append(cleaned)
            if result:
                return result

        # Split on sentence boundaries (handling abbreviations)
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\'\[])', text)
        result = []
        for s in sentences:
            s_clean = s.strip()
            if s_clean:
                result.append(s_clean)
        return result if result else [text]

    @staticmethod
    def _classify_requirement_type(text: str, section: str) -> str:
        combined = f"{section} {text}".lower()
        if any(w in combined for w in ["auth", "login", "password", "session", "jwt", "credential", "2fa", "mfa", "logout"]):
            return "Authentication & Security"
        elif any(w in combined for w in ["permission", "role", "admin", "privilege", "access control", "rbac", "authorized"]):
            return "Authorization & Access"
        elif any(w in combined for w in ["performance", "response time", "latency", "throughput", "concurrency", "sla", "load"]):
            return "Performance & Scalability"
        elif any(w in combined for w in ["cancel", "refund", "return", "payment", "checkout", "order", "cart", "invoice", "billing"]):
            return "Business & Transaction"
        elif any(w in combined for w in ["retention", "backup", "gdpr", "audit", "compliance", "log", "archive"]):
            return "Data Retention & Compliance"
        elif any(w in combined for w in ["notification", "email", "sms", "alert", "push"]):
            return "Notification & Messaging"
        elif any(w in combined for w in ["ui", "interface", "display", "screen", "button", "responsive", "mobile"]):
            return "User Interface"
        return "Functional Requirement"

    @staticmethod
    def _determine_priority(text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["must", "shall", "mandatory", "required", "strictly", "critical", "must not", "shall not"]):
            return "Must Have / High"
        elif any(w in text_lower for w in ["should", "recommended", "expected", "ought to"]):
            return "Should Have / Medium"
        elif any(w in text_lower for w in ["may", "optional", "can", "could", "preferred"]):
            return "Could Have / Low"
        return "Medium"

    @staticmethod
    def _extract_entities(text: str) -> List[str]:
        """Extract key business entities and numerical constraints."""
        entities = []
        # Numbers with units (e.g. 15 minutes, 30 days, 200ms)
        quantities = re.findall(r'\b\d+\s*(?:minutes?|hours?|days?|seconds?|ms|percent|%|users?|attempts?)\b', text, re.IGNORECASE)
        entities.extend(quantities)
        
        # Actors/Roles
        roles = re.findall(r'\b(admin|administrator|customer|user|guest|client|manager|operator|supervisor|system)\b', text, re.IGNORECASE)
        entities.extend(list(set(r.capitalize() for r in roles)))
        
        # Actions
        actions = re.findall(r'\b(reset|cancel|refund|authenticate|logout|login|delete|update|export|verify)\b', text, re.IGNORECASE)
        entities.extend(list(set(a.lower() for a in actions)))
        
        return list(dict.fromkeys(entities))
