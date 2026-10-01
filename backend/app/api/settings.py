from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel
from typing import Optional
from app.models.schemas import ProviderSettings, UserProfile
from app.services.auth_service import get_current_user
from app.services.ai_providers.provider_factory import AIProviderFactory

router = APIRouter(prefix="/api/settings", tags=["Settings"])

class UpdateProviderRequest(BaseModel):
    provider_name: str
    api_key: Optional[str] = None

@router.get("/ai", response_model=ProviderSettings)
async def get_ai_settings(current_user: UserProfile = Depends(get_current_user)):
    """Returns AI provider availability and active configuration."""
    status = AIProviderFactory.get_provider_status()
    return ProviderSettings(**status)

@router.post("/ai")
async def update_ai_settings(
    payload: UpdateProviderRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """Switches the active AI provider (local, openai, gemini)."""
    AIProviderFactory.set_active_provider(payload.provider_name)
    return {
        "message": f"Active AI provider updated to '{payload.provider_name}'",
        "current_provider": payload.provider_name
    }
