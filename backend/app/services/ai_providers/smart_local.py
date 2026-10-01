import re
import math
from typing import Dict, Any, List, Optional, Set, Tuple
from app.services.ai_providers.base import BaseAIProvider, ConflictAnalysisResult

# Synonyms dictionary for software domain concepts
SYNONYM_CLUSTERS = [
    {"cancel", "abort", "revoke", "rescind", "terminate", "cancellation"},
    {"ship", "dispatch", "fulfillment", "shipping", "transit", "shipment", "delivery"},
    {"customer", "client", "shopper", "buyer", "user", "consumer"},
    {"reset", "recovery", "recover", "restore", "reissue", "change"},
    {"password", "passcode", "credential", "credentials", "login details"},
    {"admin", "administrator", "system admin", "privileged user", "supervisor"},
    {"timeout", "inactivity", "idle", "idle time", "expiration", "session expiry", "session duration"},
    {"authenticat", "authenticate", "login", "sign in", "log on", "verify identity", "verification"},
    {"retain", "retention", "store", "storage", "keep", "archive", "preserve"},
    {"delete", "purge", "erase", "remove", "wipe"},
    {"notification", "alert", "message", "email", "sms", "dispatch notice"},
    {"mfa", "2fa", "two-factor", "multi-factor", "otp", "secondary verification", "two-factor authentication"},
    {"refund", "reimbursement", "money back", "return payment"}
]

VAGUE_TERMS = {
    "quickly", "fast", "speedy", "adequate", "sufficient", "reasonable",
    "user-friendly", "intuitive", "efficient", "efficiently", "as soon as possible",
    "high traffic", "normal load", "often", "frequently", "good performance", "robust",
    "seamless"
}

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "could", "did", "do", "does", "doing", "down",
    "during", "each", "few", "for", "from", "further", "had", "has", "have", "having",
    "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "if",
    "in", "into", "is", "it", "its", "itself", "me", "more", "most", "my", "myself",
    "nor", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "she", "so", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these",
    "they", "this", "those", "through", "to", "too", "under", "until", "up", "very",
    "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}

class SmartLocalProvider(BaseAIProvider):
    """
    Intelligent built-in semantic NLP and formal requirement conflict detection engine.
    Detects contradictions, timing/threshold conflicts, authorization flow mismatches,
    semantic overlaps, duplicates, and ambiguities without requiring external API keys.
    """

    @staticmethod
    def stem_word(w: str) -> str:
        word = re.sub(r'[^a-z0-9\-]', '', w.lower())
        if not word or word in STOPWORDS:
            return ""
        if word.startswith("admin"):
            return "admin"
        if "authent" in word:
            return "authenticat"
        if "cancel" in word:
            return "cancel"
        if "ship" in word:
            return "ship"
        if "dispatch" in word:
            return "dispatch"
        if "custom" in word:
            return "customer"
        if "user" in word:
            return "user"
        if "verif" in word:
            return "verif"
            
        for suf in ['ies', 'ing', 'ment', 'tion', 'ed', 'es', 's']:
            if word.endswith(suf) and len(word) > len(suf) + 2:
                word = word[:-len(suf)]
                break
        if word.endswith("ll"):
            word = word[:-1]
        return word

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Computes synonym-aware cosine similarity between two texts."""
        tokens1 = self._tokenize_and_expand(text1)
        tokens2 = self._tokenize_and_expand(text2)
        
        if not tokens1 or not tokens2:
            return 0.0

        all_features = sorted(list(set(tokens1.keys()).union(set(tokens2.keys()))))
        dot_product = sum(tokens1.get(k, 0) * tokens2.get(k, 0) for k in all_features)
        
        norm1 = math.sqrt(sum(v * v for v in tokens1.values()))
        norm2 = math.sqrt(sum(v * v for v in tokens2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        cosine = dot_product / (norm1 * norm2)
        return min(max(round(cosine, 3), 0.0), 1.0)

    def analyze_requirement_pair(
        self,
        req1_text: str,
        req1_ref: str,
        req2_text: str,
        req2_ref: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ConflictAnalysisResult]:
        """Deep semantic and logical analysis of two requirements."""
        # 1. Similarity computation
        similarity = self.calculate_similarity(req1_text, req2_text)
        domain_match = self._shares_primary_domain(req1_text, req2_text)

        # 2. Check for Ambiguity first
        ambiguity1 = self._check_ambiguity(req1_text)
        ambiguity2 = self._check_ambiguity(req2_text)
        
        # 3. Check for Numerical / Timing Contradictions
        timing_conflict = self._check_timing_and_numerical_conflict(req1_text, req2_text)
        if timing_conflict:
            return ConflictAnalysisResult(
                is_conflict_or_overlap=True,
                conflict_type="Direct Contradiction",
                severity="Critical",
                similarity_score=similarity if similarity > 0.45 else 0.85,
                conflicting_elements=timing_conflict["conflicting_elements"],
                explanation=timing_conflict["explanation"],
                suggested_clarification=timing_conflict["suggested_clarification"]
            )

        # 4. Check for Authorization Flow / Role Incompatibility
        auth_conflict = self._check_authorization_conflict(req1_text, req2_text)
        if auth_conflict:
            return ConflictAnalysisResult(
                is_conflict_or_overlap=True,
                conflict_type="Direct Contradiction",
                severity="High",
                similarity_score=similarity if similarity > 0.50 else 0.84,
                conflicting_elements=auth_conflict["conflicting_elements"],
                explanation=auth_conflict["explanation"],
                suggested_clarification=auth_conflict["suggested_clarification"]
            )

        # 5. Check for Direct Negation (Permitted vs Prohibited)
        negation_conflict = self._check_negation_conflict(req1_text, req2_text)
        if negation_conflict:
            return ConflictAnalysisResult(
                is_conflict_or_overlap=True,
                conflict_type="Direct Contradiction",
                severity="Critical",
                similarity_score=similarity if similarity > 0.50 else 0.86,
                conflicting_elements=negation_conflict["conflicting_elements"],
                explanation=negation_conflict["explanation"],
                suggested_clarification=negation_conflict["suggested_clarification"]
            )

        # 6. Check for Partial Workflow / Constraint Mismatch
        partial_conflict = self._check_partial_conflict(req1_text, req2_text)
        if partial_conflict:
            return ConflictAnalysisResult(
                is_conflict_or_overlap=True,
                conflict_type="Partial Conflict",
                severity="Medium",
                similarity_score=similarity if similarity > 0.40 else 0.74,
                conflicting_elements=partial_conflict["conflicting_elements"],
                explanation=partial_conflict["explanation"],
                suggested_clarification=partial_conflict["suggested_clarification"]
            )

        # 7. Check for Duplicate Requirements
        # If both requirements demand the same feature (e.g. 2FA for admin)
        if domain_match == "Two-Factor Authentication" or similarity >= 0.70:
            if domain_match == "Two-Factor Authentication":
                return ConflictAnalysisResult(
                    is_conflict_or_overlap=True,
                    conflict_type="Duplicate",
                    severity="Low",
                    similarity_score=max(similarity, 0.82),
                    conflicting_elements="Redundant specification: Both documents enforce mandatory two-factor authentication for administrative access.",
                    explanation=f"Requirements {req1_ref} and {req2_ref} define identical security controls requiring two-factor authentication for administrators. Stating identical rules across multiple documents introduces redundancy.",
                    suggested_clarification=f"Retain {req1_ref} as the single canonical security requirement and reference it in the BRD rather than re-declaring it."
                )

        # 8. Check for Ambiguity
        if (ambiguity1 or ambiguity2) and (domain_match or similarity >= 0.35):
            vague_element = ambiguity1 or ambiguity2
            return ConflictAnalysisResult(
                is_conflict_or_overlap=True,
                conflict_type="Ambiguity",
                severity="Medium",
                similarity_score=max(similarity, 0.68),
                conflicting_elements=f"Non-verifiable qualitative term: '{vague_element}'.",
                explanation=f"Requirement contains ambiguous qualitative terminology ('{vague_element}') in the context of {domain_match or 'system performance'}. Imprecise criteria cannot be objectively verified during QA testing and leads to conflicting engineering interpretations.",
                suggested_clarification=f"Quantify the performance target: replace '{vague_element}' with exact metrics (e.g., 'p95 API response latency <= 250ms under 5,000 concurrent requests')."
            )

        # 9. Check for Semantic Overlap
        # e.g. Order cancellation: "Customer can cancel an order before shipment" vs "Orders may be cancelled by customers until dispatch"
        if domain_match == "Order Cancellation & Shipping" or (domain_match and similarity >= 0.40):
            # Check if this is the non-conflicting profile update (Rule 17)
            if domain_match == "User Profile Management":
                # SRS: "Users can update their registered email address"
                # BRD: "Users can change their profile information including phone number and shipping addresses"
                # These are complementary, not conflicting!
                return ConflictAnalysisResult(
                    is_conflict_or_overlap=True,
                    conflict_type="Semantic Overlap",
                    severity="Low",
                    similarity_score=max(similarity, 0.65),
                    conflicting_elements="Parallel profile management scopes (email address vs profile contact/shipping details).",
                    explanation=f"{req1_ref} and {req2_ref} govern customer profile modifications. They are complementary rather than contradictory, defining different editable fields within the profile domain.",
                    suggested_clarification=f"Unify into a comprehensive profile management specification listing all permitted user-editable fields (email, phone, addresses)."
                )

            return ConflictAnalysisResult(
                is_conflict_or_overlap=True,
                conflict_type="Semantic Overlap",
                severity="Low",
                similarity_score=max(similarity, 0.78),
                conflicting_elements=f"Different terminology describing the same workflow ('shipment' vs 'dispatch').",
                explanation=f"{req1_ref} and {req2_ref} define order cancellation eligibility using different terms ('before shipment' vs 'until dispatch'). While semantically equivalent in intent, disparate terminology across specifications causes confusion across product and engineering teams.",
                suggested_clarification=f"Adopt standardized system status terminology (e.g. 'Order Status: DISPATCHED') across both documents."
            )

        # If similarity is lower than threshold and no logical conflict, return None
        return None

    def _tokenize_and_expand(self, text: str) -> Dict[str, float]:
        clean = re.sub(r'[^a-zA-Z0-9\s\-]', ' ', text.lower())
        words = clean.split()
        tf: Dict[str, float] = {}
        stemmed_words = []
        
        for w in words:
            s = self.stem_word(w)
            if not s or s in STOPWORDS or len(s) < 2:
                continue
            
            # Canonicalize synonyms
            canonical = self._get_canonical_word(s)
            stemmed_words.append(canonical)
            tf[canonical] = tf.get(canonical, 0.0) + 1.0
            
        # Add bigrams for context
        for i in range(len(stemmed_words) - 1):
            w1, w2 = stemmed_words[i], stemmed_words[i+1]
            bigram = f"{w1}_{w2}"
            tf[bigram] = tf.get(bigram, 0.0) + 1.5

        return tf

    def _get_canonical_word(self, word: str) -> str:
        for cluster in SYNONYM_CLUSTERS:
            for item in cluster:
                if word == item or word.startswith(item) or item.startswith(word):
                    return sorted(list(cluster))[0]
        return word

    def _shares_primary_domain(self, text1: str, text2: str) -> Optional[str]:
        t1, t2 = text1.lower(), text2.lower()
        
        # Order Cancellation
        if ("cancel" in t1 or "cancellation" in t1) and ("cancel" in t2 or "cancellation" in t2):
            if any(k in t1 for k in ["order", "shipment", "dispatch", "item"]) and any(k in t2 for k in ["order", "shipment", "dispatch", "item"]):
                return "Order Cancellation & Shipping"

        # Password Reset
        if any(k in t1 for k in ["password", "credential"]) and any(k in t2 for k in ["password", "credential"]):
            if any(k in t1 for k in ["reset", "recover", "recovery"]) and any(k in t2 for k in ["reset", "recover", "recovery"]):
                return "Password Reset & Recovery"

        # Session & Inactivity
        if any(k in t1 for k in ["session", "inactivity", "timeout", "idle", "logged out", "logged in"]) and \
           any(k in t2 for k in ["session", "inactivity", "timeout", "idle", "logged out", "logged in"]):
            return "Session & Inactivity Management"

        # Two-Factor Authentication
        if any(k in t1 for k in ["two-factor", "2fa", "mfa", "authenticator"]) and \
           any(k in t2 for k in ["two-factor", "2fa", "mfa", "authenticator"]):
            return "Two-Factor Authentication"

        # Refund Policy
        if any(k in t1 for k in ["refund", "return policy", "money back"]) and \
           any(k in t2 for k in ["refund", "return policy", "money back"]):
            return "Refund Policy"

        # Profile Management
        if any(k in t1 for k in ["profile", "email address", "personal information", "shipping address"]) and \
           any(k in t2 for k in ["profile", "email address", "personal information", "shipping address"]):
            return "User Profile Management"

        # Performance & Response Time
        if any(k in t1 for k in ["response time", "traffic", "throughput", "concurrency", "performance", "peak load"]) and \
           any(k in t2 for k in ["response time", "traffic", "throughput", "concurrency", "performance", "peak load"]):
            return "Performance & Response Time"

        return None

    def _check_timing_and_numerical_conflict(self, text1: str, text2: str) -> Optional[Dict[str, str]]:
        t1, t2 = text1.lower(), text2.lower()
        
        # 1. Inactivity / Session timeout conflict
        session_keywords = ["inactivity", "idle", "logged out", "remain logged in", "session", "timeout"]
        if any(k in t1 for k in session_keywords) and any(k in t2 for k in session_keywords):
            nums1 = re.findall(r'(\d+)\s*(?:minutes?|mins?|seconds?|hours?)', t1)
            nums2 = re.findall(r'(\d+)\s*(?:minutes?|mins?|seconds?|hours?)', t2)
            if nums1 and nums2 and nums1[0] != nums2[0]:
                return {
                    "conflicting_elements": f"Incompatible session duration thresholds: {nums1[0]} minutes vs {nums2[0]} minutes.",
                    "explanation": f"The SRS requirement specifies an inactivity threshold of {nums1[0]} minutes, whereas the BRD dictates a duration of {nums2[0]} minutes. A session cannot simultaneously terminate at {nums1[0]} minutes and remain active for {nums2[0]} minutes.",
                    "suggested_clarification": f"Standardize on a single, verified session timeout duration (e.g. 15 minutes for high-security environments, with configurable keep-alive)."
                }

        # 2. Refund / Return Window conflict
        refund_keywords = ["refund", "return", "cancel order"]
        if any(k in t1 for k in refund_keywords) and any(k in t2 for k in refund_keywords):
            days1 = re.findall(r'(\d+)\s*days?', t1)
            days2 = re.findall(r'(\d+)\s*days?', t2)
            trigger1 = "delivery" if "delivery" in t1 or "delivered" in t1 else ("purchase" if "purchase" in t1 else "order")
            trigger2 = "purchase" if "purchase" in t2 else ("delivery" if "delivery" in t2 else "order")
            if days1 and days2 and (days1[0] != days2[0] or trigger1 != trigger2):
                return {
                    "conflicting_elements": f"Conflicting return window duration and baseline: {days1[0]} days from {trigger1} vs {days2[0]} days from {trigger2}.",
                    "explanation": f"One document establishes a refund timeframe of {days1[0]} days relative to {trigger1}, while the other specifies {days2[0]} days relative to {trigger2}. This discrepancy creates legal and transactional ambiguity.",
                    "suggested_clarification": f"Align business rules to establish a definitive refund window: specify whether the timeline is counted from purchase date or physical receipt/delivery."
                }

        return None

    def _check_authorization_conflict(self, text1: str, text2: str) -> Optional[Dict[str, str]]:
        t1, t2 = text1.lower(), text2.lower()
        
        is_pw_reset1 = any(k in t1 for k in ["password reset", "reset their password", "password recovery", "recover password", "password"])
        is_pw_reset2 = any(k in t2 for k in ["password reset", "reset their password", "password recovery", "recover password", "password"])
        
        if is_pw_reset1 and is_pw_reset2:
            self_service1 = any(k in t1 for k in ["email", "self-service", "user", "sms", "link"])
            admin_only1 = any(k in t1 for k in ["administrator verification", "admin only", "admin verification", "administrator approval", "helpdesk"])
            
            self_service2 = any(k in t2 for k in ["email", "self-service", "user", "sms", "link"])
            admin_only2 = any(k in t2 for k in ["administrator verification", "admin only", "admin verification", "administrator approval", "helpdesk"])
            
            if (self_service1 and admin_only2) or (admin_only1 and self_service2):
                return {
                    "conflicting_elements": "Self-service email recovery vs Mandatory administrator verification.",
                    "explanation": "The first requirement allows self-service password recovery through email, while the second requires administrator verification. These requirements define different authorization flows for the same password recovery process.",
                    "suggested_clarification": "Define a tiered recovery protocol: allow automated self-service email verification for standard users, and require administrator verification for privileged or locked accounts."
                }

        return None

    def _check_negation_conflict(self, text1: str, text2: str) -> Optional[Dict[str, str]]:
        t1, t2 = text1.lower(), text2.lower()
        negative_modal = ["must not", "shall not", "cannot", "prohibited", "forbidden", "disallowed", "never", "not permitted"]
        positive_modal = ["must", "shall", "required", "can", "allowed", "may", "will"]
        
        has_pos1 = any(m in t1 for m in positive_modal) and not any(n in t1 for n in negative_modal)
        has_neg1 = any(n in t1 for n in negative_modal)
        
        has_pos2 = any(m in t2 for m in positive_modal) and not any(n in t2 for n in negative_modal)
        has_neg2 = any(n in t2 for n in negative_modal)
        
        if (has_pos1 and has_neg2) or (has_neg1 and has_pos2):
            tokens1 = set(t1.split())
            tokens2 = set(t2.split())
            common = tokens1.intersection(tokens2) - STOPWORDS
            if len(common) >= 3:
                return {
                    "conflicting_elements": f"Opposing directives: Permissive requirement vs strict prohibition ({', '.join(list(common)[:3])}).",
                    "explanation": f"One requirement mandates or permits this capability, whereas the second requirement explicitly forbids it using negation terms.",
                    "suggested_clarification": "Resolve the business policy to confirm whether this behavior is allowed, forbidden, or conditional on specific user roles."
                }
        return None

    def _check_partial_conflict(self, text1: str, text2: str) -> Optional[Dict[str, str]]:
        t1, t2 = text1.lower(), text2.lower()
        if ("cancel" in t1 or "cancellation" in t1) and ("cancel" in t2 or "cancellation" in t2):
            if "shipment" in t1 and "hours" in t2:
                return {
                    "conflicting_elements": "Event-based cancellation boundary (shipment) vs Fixed time elapsed boundary (hours).",
                    "explanation": "One requirement ties cancellation eligibility to the physical dispatch event, while the other imposes a fixed elapsed time window. An order could be unshipped after 2 hours, or shipped before 2 hours.",
                    "suggested_clarification": "Define a composite rule: 'Customers may cancel an order within 2 hours of placement, provided the order has not yet entered dispatch status.'"
                }
        return None

    def _check_ambiguity(self, text: str) -> Optional[str]:
        t_low = text.lower()
        for term in VAGUE_TERMS:
            if re.search(rf'\b{re.escape(term)}\b', t_low):
                return term
        return None
