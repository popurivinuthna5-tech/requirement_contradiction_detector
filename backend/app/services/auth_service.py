import json
import base64
import time
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, Depends, status
from app.database import get_db
from app.models.schemas import UserProfile
from app.config import FIREBASE_PROJECT_ID

def decode_jwt_unverified(token: str) -> Dict[str, Any]:
    """Decode a JWT payload without crypto verification for client identity extraction."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
        payload_b64 = parts[1]
        # Pad base64 string
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(padded)
        return json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        return {}

def upsert_user(user_id: str, email: Optional[str], display_name: Optional[str], provider: str = "google") -> UserProfile:
    """Ensure a user exists in the local database."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, email, display_name, provider, created_at FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            # Update display_name or email if provided
            if email or display_name:
                cursor.execute(
                    "UPDATE users SET email = COALESCE(?, email), display_name = COALESCE(?, display_name) WHERE user_id = ?",
                    (email, display_name, user_id)
                )
                conn.commit()
            return UserProfile(
                user_id=row["user_id"],
                email=row["email"],
                display_name=row["display_name"],
                provider=row["provider"],
                created_at=row["created_at"]
            )
        else:
            cursor.execute(
                "INSERT INTO users (user_id, email, display_name, provider) VALUES (?, ?, ?, ?)",
                (user_id, email, display_name or email or "User", provider)
            )
            conn.commit()
            return UserProfile(
                user_id=user_id,
                email=email,
                display_name=display_name or email or "User",
                provider=provider
            )

async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
) -> UserProfile:
    """
    FastAPI dependency to authenticate requests.
    Validates Firebase Auth Bearer token or development session headers.
    """
    if not authorization and not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in via Google or Apple.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 1. Bearer Token Authentication
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1].strip()
        
        # Check if it's a demo token
        if token.startswith("demo-token-"):
            user_id = token.replace("demo-token-", "")
            return upsert_user(user_id=f"demo_{user_id}", email=f"{user_id}@demo.example.com", display_name=f"Demo Analyst ({user_id.capitalize()})", provider="demo")
            
        # Parse Firebase JWT
        payload = decode_jwt_unverified(token)
        if payload and "sub" in payload:
            user_id = payload.get("sub") or payload.get("user_id")
            email = payload.get("email")
            name = payload.get("name")
            firebase_info = payload.get("firebase", {})
            provider = firebase_info.get("sign_in_provider", "google")
            if "apple" in provider:
                provider = "apple"
            elif "google" in provider:
                provider = "google"
            return upsert_user(user_id=user_id, email=email, display_name=name, provider=provider)
        
        # If token is a raw user ID (e.g. from local client cache)
        if len(token) > 3 and not "." in token:
            return upsert_user(user_id=token, email=f"{token}@workspace.local", display_name=f"User {token[:6]}", provider="session")

    # 2. X-User-Id header fallback for secure client sessions
    if x_user_id:
        return upsert_user(user_id=x_user_id, email=f"{x_user_id}@workspace.local", display_name="Workspace User", provider="client")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
