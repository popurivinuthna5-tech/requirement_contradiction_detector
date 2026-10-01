from typing import Optional, List, Dict
from app.services.ai_providers.base import BaseAIProvider
from app.services.ai_providers.smart_local import SmartLocalProvider
from app.services.ai_providers.openai_provider import OpenAIProvider
from app.services.ai_providers.gemini_provider import GeminiProvider
from app.config import AI_PROVIDER, OPENAI_API_KEY, GEMINI_API_KEY, CLAUDE_API_KEY, OLLAMA_BASE_URL

class AIProviderFactory:
    _instance: Optional[BaseAIProvider] = None
    _current_provider_name: str = AI_PROVIDER

    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> BaseAIProvider:
        name = (provider_name or cls._current_provider_name or "local").lower()
        
        if name == "openai":
            return OpenAIProvider()
        elif name == "gemini":
            return GeminiProvider()
        elif name == "local":
            return SmartLocalProvider()
        else:
            return SmartLocalProvider()

    @classmethod
    def set_active_provider(cls, provider_name: str):
        cls._current_provider_name = provider_name.lower()

    @classmethod
    def get_provider_status(cls) -> Dict[str, Any]:
        return {
            "active_provider": cls._current_provider_name,
            "available_providers": ["local", "openai", "gemini"],
            "openai_configured": bool(OPENAI_API_KEY),
            "gemini_configured": bool(GEMINI_API_KEY),
            "claude_configured": bool(CLAUDE_API_KEY),
            "ollama_url": OLLAMA_BASE_URL
        }
