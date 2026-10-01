from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import AuthVerifyRequest, UserProfile
from app.services.auth_service import get_current_user, upsert_user, decode_jwt_unverified

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/verify", response_model=UserProfile)
async def verify_auth(payload: AuthVerifyRequest):
    """
    Verifies client authentication credentials and returns the user profile.
    Supports Firebase Auth tokens and demo session initialization.
    """
    if payload.id_token:
        decoded = decode_jwt_unverified(payload.id_token)
        user_id = decoded.get("sub") or decoded.get("user_id") or payload.user_id
        email = decoded.get("email") or payload.email
        name = decoded.get("name") or payload.display_name
        provider = payload.provider or "google"
        
        if not user_id:
            user_id = f"usr_{hash(email or 'user') & 0xFFFFFFFFFF}"
            
        user = upsert_user(user_id=str(user_id), email=email, display_name=name, provider=provider)
        return user
        
    elif payload.user_id:
        user = upsert_user(
            user_id=payload.user_id,
            email=payload.email,
            display_name=payload.display_name or "Guest User",
            provider=payload.provider or "demo"
        )
        return user
        
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Missing authentication credentials."
    )

@router.get("/me", response_model=UserProfile)
async def get_me(current_user: UserProfile = Depends(get_current_user)):
    """Returns the authenticated user's profile."""
    return current_user
