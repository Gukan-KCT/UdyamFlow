# AI Module
from app.ai.ollama_service import generate_insight, generate_chat_reply
from app.ai.prompt import get_fallback_insight

__all__ = ["generate_insight", "generate_chat_reply", "get_fallback_insight"]
