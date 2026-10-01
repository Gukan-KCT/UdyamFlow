from datetime import datetime
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

def get_now() -> datetime:
    """Return real clock, or DEMO_NOW environment override if provided."""
    demo_now = os.getenv("DEMO_NOW")
    if demo_now:
        return datetime.fromisoformat(demo_now)
    return datetime.now()


DEMO_NOW = os.getenv("DEMO_NOW")
REFERENCE_NOW = DEMO_NOW or get_now().isoformat()

ROT_THRESHOLDS_DAYS = {
    "WARNING": 15,
    "HIGH": 30,
    "CRITICAL": 45,
    "CAMPAIGN": 90,
}

LOOP_MIN_ROUND_TRIPS = 2
LOOP_WINDOW_DAYS = 30

EXCLUDED_STATUSES = {"Closed", "Archived"}

# AI Provider: ollama | openrouter | none
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower().strip()

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60"))

# OpenRouter settings
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen-2.5-7b-instruct")
OPENROUTER_TIMEOUT = float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "30"))

AI_CALL_DELAY_SECONDS = float(os.getenv("AI_CALL_DELAY_SECONDS", "1.5"))

# Application Secret Key for JWT / Sessions
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "udyamflow-development-secret-key-32-chars-min-sih")
