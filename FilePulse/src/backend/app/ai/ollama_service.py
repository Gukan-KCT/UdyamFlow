import json
import uuid
from datetime import datetime

import httpx

from app.ai.prompt import OllamaResponse, get_fallback_insight
from app.models import AiInsight, Alert, Event, FileRecord
from config import (
    AI_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    REFERENCE_NOW,
)

_OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"


async def generate_insight_ollama(
    alert: Alert,
    file_record: FileRecord,
    events: list[Event],
    compound: bool = False,
) -> AiInsight:
    """Calls local Ollama instance for insight generation."""
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

    payload = {
        "model": OLLAMA_MODEL,
        "system": "You are an administrative workflow analyst. Use only the facts provided. Do not invent information. Use neutral language — say 'appears' or 'likely.' Never use 'negligent', 'lazy', or 'incompetent'. Respond with valid JSON only.",
        "prompt": f"Analyze this e-Office file alert. File Facts: {json.dumps(facts)}. Respond with ONLY a JSON object with keys: plain_language_summary, likely_blocker, recommended_action, confidence (Low/Medium/High).",
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
            "top_p": 0.9,
            "num_predict": 250,
            "num_ctx": 2048,
        },
    }

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

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(_OLLAMA_URL, json=payload)
            response.raise_for_status()
            parsed = OllamaResponse.model_validate_json(response.json().get("response", "{}"))

        return AiInsight(
            insight_id=insight_id,
            alert_id=alert.alert_id,
            plain_language_summary=parsed.plain_language_summary,
            likely_blocker=parsed.likely_blocker,
            recommended_action=parsed.recommended_action,
            confidence=parsed.confidence,
            source="ollama",
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


async def generate_chat_reply_ollama(prompt: str, system_prompt: str) -> str | None:
    """Send chat message to Ollama. Returns None on failure."""
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "system": system_prompt,
                    "prompt": prompt,
                    "options": {"temperature": 0},
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
    except Exception:
        return None


async def generate_insight(
    alert: Alert,
    file_record: FileRecord,
    events: list[Event],
    compound: bool = False,
) -> AiInsight:
    """
    Unified insight generator dispatched according to AI_PROVIDER env var.
    Supported: 'ollama', 'openrouter', 'none'.
    Falls back to deterministic rule-based output if none or upon error.
    """
    provider = (AI_PROVIDER or "ollama").lower().strip()

    if provider == "openrouter":
        from app.ai.openrouter_service import generate_insight_openrouter
        return await generate_insight_openrouter(alert, file_record, events, compound=compound)

    if provider == "ollama":
        return await generate_insight_ollama(alert, file_record, events, compound=compound)

    # Provider == "none" or fallback
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
    fallback = get_fallback_insight(alert_type_for_fallback, fallback_context)
    return AiInsight(
        insight_id=insight_id,
        alert_id=alert.alert_id,
        plain_language_summary=fallback.plain_language_summary,
        likely_blocker=fallback.likely_blocker,
        recommended_action=fallback.recommended_action,
        confidence=fallback.confidence,
        source="rule_based_fallback",
        generated_at=generated_at,
    )


async def generate_chat_reply(
    prompt: str,
    system_prompt: str,
    intent: str | None = None,
    context: dict | None = None,
) -> str:
    """Generate chat response respecting AI_PROVIDER, with clean rule-based fallback."""
    provider = (AI_PROVIDER or "ollama").lower().strip()

    if provider == "openrouter":
        from app.ai.openrouter_service import generate_chat_reply_openrouter
        reply = await generate_chat_reply_openrouter(prompt, system_prompt)
        if reply:
            return reply

    if provider == "ollama":
        reply = await generate_chat_reply_ollama(prompt, system_prompt)
        if reply:
            return reply

    # Rule-based fallback summary when AI engine is offline or provider is 'none'
    if context:
        if intent == "REGULATORY_GUIDANCE":
            approvals = context.get("sample_approvals", [])
            names = ", ".join([a.get("name") for a in approvals[:4]]) if approvals else "CTE, CTO, Fire NOC, Factory License"
            return (
                f"UdyamFlow Regulatory Engine: Based on statutory guidelines, applicable clearances include {names}. "
                "These approvals are governed under the Water Act 1974, Air Act 1981, and Factories Act 1948 with statutory SLAs ranging between 15 to 30 days. "
                "You can generate a customised clearance roadmap using the Checklist Wizard."
            )
        if intent == "PARALLEL_WORKFLOW":
            return (
                "UdyamFlow Parallel Workflow Architecture: Composite single-window applications route sub-clearances concurrently "
                "across the Pollution Control Board, Fire Safety Department, Factories Directorate, and DISCOM. "
                "This non-linear processing reduces critical path turnaround time by up to 65% compared to traditional sequential filing."
            )
        if intent == "INSPECTION_GUIDANCE":
            return (
                "Common Joint Inspection Framework: Instead of multiple uncoordinated visits by separate agencies, "
                "UdyamFlow synchronizes site visits into a single joint inspection on a predetermined date. "
                "Officers from PCB, Fire, and Factories submit a combined digital observation report with a unified statutory verdict."
            )
        if intent == "SCHEMES_GUIDANCE":
            schemes = context.get("active_schemes", [])
            count = len(schemes) if schemes else 4
            return (
                f"Industrial Incentives & Subsidies: There are currently {count} active state incentive programs, "
                "including Capital Investment Subsidies (up to 25%), Power Tariff Concessions (₹1.50/unit rebate), "
                "Green Energy Transition Subsidies (up to ₹25 Lakhs), and 100% Stamp Duty Exemptions. "
                "You can assess eligibility and file claims in the Incentives section."
            )
        if intent == "GRIEVANCE_GUIDANCE":
            return (
                "Statutory 3-Tier Grievance Redressal: If any clearance breaches its statutory SLA or faces unexplained inactivity, "
                "you can escalate through: Tier 1: Department Nodal Officer (7 days) -> "
                "Tier 2: District Collector / Empowered Single-Window Committee (15 days) -> "
                "Tier 3: State Single Window Appellate Authority (30 days)."
            )
        if intent == "FILE_DETAIL":
            f = context.get("file", {})
            return (
                f"File {f.get('file_id')}: '{f.get('title')}' is currently {f.get('status')} "
                f"with {f.get('current_holder')} (Priority: {f.get('priority')}). "
                f"Deadline: {f.get('deadline')}."
            )
        if intent == "DASHBOARD_SUMMARY":
            summary = context.get("summary", {})
            return (
                f"Office Overview: {summary.get('total_active_files', 0)} active files, "
                f"{summary.get('high_risk_files', 0)} high-risk items, and "
                f"{summary.get('overdue_files', 0)} overdue files as of today."
            )

    return (
        "Hello! I am UdyamFlow Copilot. How can I assist you with your industrial approvals, statutory compliance, joint inspections, or incentive schemes today?"
    )
