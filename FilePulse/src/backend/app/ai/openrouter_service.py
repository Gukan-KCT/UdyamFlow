import json
import uuid
from datetime import datetime

import httpx

from app.ai.prompt import OllamaResponse, get_fallback_insight
from app.models import AiInsight, Alert, Event, FileRecord
from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
    OPENROUTER_TIMEOUT,
    REFERENCE_NOW,
)

_OPENROUTER_CHAT_URL = f"{OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"


async def generate_insight_openrouter(
    alert: Alert,
    file_record: FileRecord,
    events: list[Event],
    compound: bool = False,
) -> AiInsight:
    """
    Calls OpenRouter API to generate a plain-language insight for a detected alert.
    Falls back to rule-based text on any failure — the dashboard never breaks.
    """
    insight_id = str(uuid.uuid4())
    generated_at = datetime.fromisoformat(REFERENCE_NOW)
    alert_type_for_fallback = "COMPOUND" if compound else alert.alert_type

    fallback_context = {
        "title": file_record.title,
        "holder": file_record.current_holder_id,
        "days": alert.days_inactive,
        "status": "Overdue" if alert.is_overdue else "Active",
        "a": alert.loop_party_a,
        "b": alert.loop_party_b,
        "trips": alert.loop_round_trips,
        "span": 30,
        "stages": alert.skipped_stages,
    }

    if not OPENROUTER_API_KEY:
        fallback = get_fallback_insight(alert_type_for_fallback, fallback_context)
        return AiInsight(
            insight_id=insight_id,
            alert_id=alert.alert_id,
            plain_language_summary=fallback.plain_language_summary,
            likely_blocker=fallback.likely_blocker,
            recommended_action=fallback.recommended_action,
            confidence=fallback.confidence,
            source="fallback",
            generated_at=generated_at,
        )

    events_str = [
        f"[{e.timestamp.strftime('%Y-%m-%d %H:%M')}] {e.action} from {e.from_user_id} to {e.to_user_id}. Note: {e.note_text}"
        for e in events
    ]

    facts = {
        "file_id": file_record.file_id,
        "title": file_record.title,
        "type": file_record.file_type,
        "priority": file_record.priority,
        "deadline_at": file_record.deadline_at.strftime("%Y-%m-%d"),
        "is_overdue": alert.is_overdue,
        "alert_type": "COMPOUND" if compound else alert.alert_type,
        "severity": alert.severity,
        "days_inactive": alert.days_inactive,
        "loop_round_trips": alert.loop_round_trips,
        "skipped_stages": alert.skipped_stages,
        "last_events": events_str,
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "FilePulse",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an administrative workflow analyst. Use only the facts provided. "
                    "Do not invent information. Use neutral language — say 'appears' or 'likely.' "
                    "Never use 'negligent', 'lazy', or 'incompetent'. Respond with valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Analyze this e-Office file alert. File Facts: {json.dumps(facts)}. "
                    "Respond with ONLY a JSON object with keys: "
                    "plain_language_summary, likely_blocker, recommended_action, confidence (Low/Medium/High)."
                ),
            },
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient(timeout=OPENROUTER_TIMEOUT) as client:
            response = await client.post(_OPENROUTER_CHAT_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = OllamaResponse.model_validate_json(content)

        return AiInsight(
            insight_id=insight_id,
            alert_id=alert.alert_id,
            plain_language_summary=parsed.plain_language_summary,
            likely_blocker=parsed.likely_blocker,
            recommended_action=parsed.recommended_action,
            confidence=parsed.confidence,
            source="openrouter",
            generated_at=generated_at,
        )
    except Exception:
        fallback = get_fallback_insight(alert_type_for_fallback, fallback_context)
        return AiInsight(
            insight_id=insight_id,
            alert_id=alert.alert_id,
            plain_language_summary=fallback.plain_language_summary,
            likely_blocker=fallback.likely_blocker,
            recommended_action=fallback.recommended_action,
            confidence=fallback.confidence,
            source="fallback",
            generated_at=generated_at,
        )


async def generate_chat_reply_openrouter(prompt: str, system_prompt: str) -> str | None:
    """Send chat message to OpenRouter. Returns None on failure."""
    if not OPENROUTER_API_KEY:
        return None
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "FilePulse",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
    }
    try:
        async with httpx.AsyncClient(timeout=OPENROUTER_TIMEOUT) as client:
            response = await client.post(_OPENROUTER_CHAT_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None
