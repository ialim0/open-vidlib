"""Question Decomposition Orchestrator.

Detects multi-part queries, dispatches sub-questions through the existing agent loop
independently, synthesizes coherent composite answers, and verifies complete coverage.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.llm_client import get_llm_client, get_llm_model, get_llm_provider, get_mistral_client
from app.services.agent_chat_loop import run_agent_loop, INSUFFICIENT_EVIDENCE, _now, _jsonable, _content

logger = logging.getLogger(__name__)
TRAJECTORY_DIR = Path(os.getenv("AGENT_TRAJECTORY_DIR", "trajectories"))


def detect_decomposition(client: Any, user_message: str) -> list[str]:
    """Classify if a user message has multiple distinct sub-questions needing separate evidence."""
    if not client:
        return []

    prompt = f"""You are an educational query analyzer. Determine if the student's request is a multi-part query requiring separate sub-question lookups or multiple distinct tasks.
If it is a single question or task, return JSON:
{{"is_multipart": false, "sub_questions": []}}

If it contains multiple distinct sub-questions or tasks (such as "Find where X is introduced, then explain Y and cite both" or "Which dimensions make the pyramid an achievement and when was it built?"), split it into 2-3 focused sub-questions:
{{"is_multipart": true, "sub_questions": ["sub-question 1", "sub-question 2"]}}

Student request: {user_message}
Return valid JSON only."""

    try:
        response = client.chat.complete(
            model=get_llm_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content_text = _content(response.choices[0].message.content)
        data = json.loads(content_text)
        if data.get("is_multipart") and isinstance(data.get("sub_questions"), list):
            sub_qs = [str(q).strip() for q in data["sub_questions"] if str(q).strip()]
            if len(sub_qs) >= 2:
                return sub_qs
    except Exception as exc:
        logger.warning("Decomposition detection failed; falling back to single loop: %s", exc)

    return []


def compose_sub_answers(client: Any, user_message: str, sub_questions: list[str], sub_results: list[dict[str, Any]]) -> str:
    """Synthesize sub-answers into one coherent final response preserving all timestamp citations."""
    sub_answer_blocks = []
    for i, (q, res) in enumerate(zip(sub_questions, sub_results), 1):
        ans = res.get("answer") or res.get("content") or INSUFFICIENT_EVIDENCE
        sub_answer_blocks.append(f"Sub-question {i}: {q}\nSub-answer {i}: {ans}")

    if not client:
        valid_answers = [
            res.get("answer") or res.get("content") or ""
            for res in sub_results
            if (res.get("answer") or res.get("content") or "") != INSUFFICIENT_EVIDENCE
        ]
        return " ".join(valid_answers).strip() or INSUFFICIENT_EVIDENCE

    prompt = f"""You are Coumba, an AI video tutor. Synthesize the following sub-answers into a single, well-structured final answer to the student's original request.

Original student request: {user_message}

Sub-answers retrieved from the video:
{chr(10).join(sub_answer_blocks)}

Requirements:
1. Retain all exact [MM:SS] timestamp citations from the sub-answers.
2. Directly answer all parts of the student's request in a unified, natural response.
3. If any sub-part could not be found, explicitly state what information was missing rather than omitting it.
4. Do not invent any facts or timestamps outside the provided sub-answers.
5. Preserve the language requested by the student (e.g. Wolof, Pulaar/Fulfulde, Bambara, French, or English)."""

    try:
        response = client.chat.complete(
            model=get_llm_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return _content(response.choices[0].message.content).strip()
    except Exception as exc:
        logger.warning("Answer synthesis failed; concatenating sub-answers: %s", exc)
        valid_answers = [
            res.get("answer") or res.get("content") or ""
            for res in sub_results
            if (res.get("answer") or res.get("content") or "") != INSUFFICIENT_EVIDENCE
        ]
        return " ".join(valid_answers).strip() or INSUFFICIENT_EVIDENCE


def verify_composite(
    client: Any,
    user_message: str,
    answer: str,
    sub_questions: list[str],
    evidence_times: set[int]
) -> dict[str, Any]:
    """Verify that the synthesized answer is grounded in evidence and addresses each sub-part."""
    cited = {
        int(minutes) * 60 + int(seconds)
        for minutes, seconds in re.findall(r"\[(\d{1,3}):(\d{2})\]", answer)
    }
    citation_ok = not evidence_times or bool(cited & evidence_times)
    addressed = bool(answer.strip()) and answer.strip() != INSUFFICIENT_EVIDENCE

    local_check = {
        "passed": citation_ok and addressed,
        "citation_valid": citation_ok,
        "all_subparts_addressed": addressed,
        "missing_subparts": [] if addressed else sub_questions,
        "feedback": "Ensure exact timestamp citations [MM:SS] are included from evidence." if not citation_ok else "Address all sub-questions.",
    }

    if not client:
        return local_check

    prompt = f"""Return JSON only with keys: passed (bool), citation_valid (bool), all_subparts_addressed (bool), missing_subparts (list of strings), feedback (string).
Original Question: {user_message}
Sub-questions: {json.dumps(sub_questions)}
Composite Answer: {answer}
Valid evidence timestamps in seconds: {sorted(evidence_times)}

A citation [MM:SS] is valid only if its seconds value is in that list. Check if EVERY sub-question is answered in the composite answer."""

    try:
        response = client.chat.complete(
            model=get_llm_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(_content(response.choices[0].message.content))
        citation_valid = bool(parsed.get("citation_valid")) or local_check["citation_valid"]
        all_addressed = bool(parsed.get("all_subparts_addressed")) and local_check["all_subparts_addressed"]
        parsed["citation_valid"] = citation_valid
        parsed["all_subparts_addressed"] = all_addressed
        parsed["passed"] = citation_valid and all_addressed
        return parsed
    except Exception as exc:
        logger.warning("Composite verification failed; using local check: %s", exc)
        return local_check


def run_orchestrated_agent(
    user_message: str,
    video_id: str,
    db: Session,
    session_id: str = "default-session"
) -> dict[str, Any]:
    """Orchestrated Agent: decomposes multi-part queries, executes each part independently, and synthesizes results."""
    request_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}_{uuid.uuid4().hex[:8]}"
    events: list[dict[str, Any]] = [
        {"event": "request", "question": user_message, "video_id": video_id, "session_id": session_id, "mode": "orchestrated", "timestamp": _now()}
    ]

    client = get_mistral_client()

    # Step 1: Decomposition detection
    sub_questions = detect_decomposition(client, user_message)

    # If no decomposition needed, fall straight through to the existing agent loop
    if not sub_questions:
        events.append({"event": "decomposition_skipped", "reason": "single_part", "timestamp": _now()})
        result = run_agent_loop(user_message, video_id, db, session_id=session_id)
        result["mode"] = "orchestrated"
        events.append({"event": "single_loop_result", "trajectory_id": result.get("trajectory_id"), "timestamp": _now()})
        
        trajectory = {"request_id": request_id, "mode": "orchestrated", "fallback_to_single_loop": True, "events": events}
        try:
            TRAJECTORY_DIR.mkdir(parents=True, exist_ok=True)
            path = TRAJECTORY_DIR / f"{request_id}.json"
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(trajectory, indent=2, ensure_ascii=False), encoding="utf-8")
            temporary.replace(path)
        except OSError as exc:
            logger.error("Could not persist orchestrator trajectory %s: %s", request_id, exc)
        return result

    # Step 2: Multi-part query execution
    events.append({"event": "decomposition_detected", "sub_questions": sub_questions, "timestamp": _now()})

    sub_results: list[dict[str, Any]] = []
    all_sources: list[dict[str, Any]] = []
    all_evidence_times: set[int] = set()
    total_calls = 0
    degraded_any = False
    sub_trajectories: list[str] = []

    for i, sub_q in enumerate(sub_questions, 1):
        sub_session = f"{session_id}_sub_{i}"
        sub_res = run_agent_loop(sub_q, video_id, db, session_id=sub_session)
        sub_results.append(sub_res)
        total_calls += int(sub_res.get("tool_call_count", 0))
        if sub_res.get("degraded"):
            degraded_any = True
        if sub_res.get("trajectory_id"):
            sub_trajectories.append(sub_res["trajectory_id"])
        for s in (sub_res.get("sources") or sub_res.get("results") or []):
            if s not in all_sources:
                all_sources.append(s)
            if "start_time" in s:
                all_evidence_times.add(int(float(s["start_time"])))

        events.append({
            "event": "sub_question_dispatched",
            "index": i,
            "sub_question": sub_q,
            "sub_trajectory_id": sub_res.get("trajectory_id"),
            "tool_call_count": sub_res.get("tool_call_count", 0),
            "verified": sub_res.get("verified"),
            "timestamp": _now(),
        })

    # Step 3: Synthesis
    synthesized_answer = compose_sub_answers(client, user_message, sub_questions, sub_results)
    events.append({"event": "synthesis", "synthesized_answer": synthesized_answer, "timestamp": _now()})

    # Step 4: Composite verification
    verification = verify_composite(client, user_message, synthesized_answer, sub_questions, all_evidence_times)
    events.append({"event": "composite_verification", "attempt": 1, "result": verification, "timestamp": _now()})

    # Retry missing sub-parts once if needed
    if not verification.get("passed") and client:
        missing = verification.get("missing_subparts") or []
        for miss_q in missing:
            retry_res = run_agent_loop(miss_q, video_id, db, session_id=f"{session_id}_retry")
            total_calls += int(retry_res.get("tool_call_count", 0))
            for s in (retry_res.get("sources") or retry_res.get("results") or []):
                if s not in all_sources:
                    all_sources.append(s)
                if "start_time" in s:
                    all_evidence_times.add(int(float(s["start_time"])))
            for idx, sq in enumerate(sub_questions):
                if sq == miss_q:
                    sub_results[idx] = retry_res
            events.append({"event": "retry_sub_question", "sub_question": miss_q, "result": retry_res.get("answer"), "timestamp": _now()})

        synthesized_answer = compose_sub_answers(client, user_message, sub_questions, sub_results)
        verification = verify_composite(client, user_message, synthesized_answer, sub_questions, all_evidence_times)
        events.append({"event": "composite_verification", "attempt": 2, "result": verification, "timestamp": _now()})

    # Step 5: Final response & trajectory persistence
    final_response = {
        "type": "qa" if all_sources else "chat",
        "content": synthesized_answer,
        "answer": synthesized_answer,
        "question": user_message,
        "sources": all_sources,
        "results": None,
        "status": None,
        "language": None,
        "voice_gender": None,
        "dub_track": None,
        "session_id": session_id,
        "mode": "orchestrated",
        "tool_call_count": total_calls,
        "steps": max(1, total_calls),
        "verified": bool(verification.get("passed")),
        "degraded": degraded_any,
        "trajectory_id": request_id,
        "sub_trajectories": sub_trajectories,
        "model_used": get_llm_model(),
        "provider_used": get_llm_provider(),
        "timestamp": datetime.now(timezone.utc),
    }

    trajectory = {
        "request_id": request_id,
        "mode": "orchestrated",
        "sub_questions": sub_questions,
        "sub_trajectories": sub_trajectories,
        "events": events,
    }
    try:
        TRAJECTORY_DIR.mkdir(parents=True, exist_ok=True)
        path = TRAJECTORY_DIR / f"{request_id}.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(trajectory, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)
    except OSError as exc:
        logger.error("Could not persist orchestrator trajectory %s: %s", request_id, exc)

    return final_response
