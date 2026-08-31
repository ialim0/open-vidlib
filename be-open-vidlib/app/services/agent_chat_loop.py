"""Bounded Mistral tool loop with verification, memory, and JSON trajectories."""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.llm_client import get_llm_client, get_llm_model, get_llm_provider, get_mistral_client, LLM_MODEL
from app.services.agent_chat_baseline import TOOLS
from app.services.dubbing_service import create_dubbed_track
from app.services.rag_qa_service import ask_video_question
from app.services.search_service import search_video

logger = logging.getLogger(__name__)
MAX_STEPS = max(1, min(int(os.getenv("AGENT_MAX_STEPS", "6")), 12))
MEMORY_TURNS = max(1, min(int(os.getenv("AGENT_MEMORY_TURNS", "4")), 10))
TRAJECTORY_DIR = Path(os.getenv("AGENT_TRAJECTORY_DIR", "trajectories"))
INSUFFICIENT_EVIDENCE = "The video does not provide enough information to answer that."

_memory: dict[tuple[str, str], list[dict[str, str]]] = {}
_memory_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if isinstance(value, list):
        return "".join(str(getattr(chunk, "text", chunk)) for chunk in value)
    return str(value)


def _history(video_id: str, session_id: str) -> list[dict[str, str]]:
    with _memory_lock:
        return list(_memory.get((video_id, session_id), []))


def _remember(video_id: str, session_id: str, user_message: str, answer: str) -> None:
    with _memory_lock:
        messages = _memory.setdefault((video_id, session_id), [])
        messages.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": answer},
        ])
        _memory[(video_id, session_id)] = messages[-(MEMORY_TURNS * 2):]


def clear_agent_memory() -> None:
    """Test/dev helper; production memory naturally resets with the API process."""
    with _memory_lock:
        _memory.clear()


def _tool_call_dict(call: Any) -> dict[str, Any]:
    function = call.function
    arguments = function.arguments
    if not isinstance(arguments, str):
        arguments = json.dumps(_jsonable(arguments))
    return {
        "id": getattr(call, "id", None) or f"call_{uuid.uuid4().hex[:12]}",
        "type": "function",
        "function": {"name": function.name, "arguments": arguments},
    }


def _execute_tool(name: str, args: dict[str, Any], user_message: str, video_id: str, db: Session, session_id: str) -> dict[str, Any]:
    if name == "search_video":
        results = search_video(video_id, args.get("query") or user_message, db)
        return {"query": args.get("query") or user_message, "results": results}
    if name == "ask_question":
        return ask_video_question(
            video_id,
            args.get("question") or user_message,
            db,
            session_id=session_id,
        )
    if name == "translate_dub":
        language = args.get("language", "fr")
        voice_gender = args.get("voice_gender", "female")
        return {
            "language": language,
            "voice_gender": voice_gender,
            "dub_track": create_dubbed_track(video_id, language, voice_gender, db),
        }
    return {"error": f"Unknown tool: {name}"}


def _evidence_times(tool_results: list[dict[str, Any]]) -> set[int]:
    timestamps: set[int] = set()
    for item in tool_results:
        result = item["result"]
        sources = result.get("sources") or result.get("results") or []
        for source in sources:
            if "start_time" in source:
                timestamps.add(int(float(source["start_time"])))
            # Include sentence-level timestamps so the verifier accepts them
            for sentence in source.get("sentences") or []:
                if "start" in sentence:
                    timestamps.add(int(float(sentence["start"])))
    return timestamps


def _local_verification(question: str, answer: str, evidence_times: set[int], citation_required: bool) -> dict[str, Any]:
    cited = {
        int(minutes) * 60 + int(seconds)
        for minutes, seconds in re.findall(r"\[(\d{1,3}):(\d{2})\]", answer)
    }
    citation_ok = not citation_required or bool(cited & evidence_times)
    addressed = bool(answer.strip()) and answer.strip() != INSUFFICIENT_EVIDENCE
    return {
        "passed": citation_ok and addressed,
        "citation_valid": citation_ok,
        "addresses_question": addressed,
        "feedback": "Use a timestamp from retrieved evidence and directly answer the learner." if not citation_ok else "Directly answer the learner using only retrieved evidence.",
    }


def _verify(client: Any, question: str, answer: str, evidence_times: set[int], citation_required: bool) -> dict[str, Any]:
    local = _local_verification(question, answer, evidence_times, citation_required)
    if not client:
        return local
    prompt = f"""Return JSON only with keys passed, citation_valid, addresses_question, feedback.
Question: {question}
Answer: {answer}
Citation required: {str(citation_required).lower()}
Valid evidence timestamps in seconds: {sorted(evidence_times)}
A citation [MM:SS] is valid only when its seconds value is in that list. The answer must directly address the question."""
    try:
        response = client.chat.complete(
            model=get_llm_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(_content(response.choices[0].message.content))
        citation_valid = bool(parsed.get("citation_valid")) or local["citation_valid"]
        addresses_question = bool(parsed.get("addresses_question")) and local["addresses_question"]
        parsed["citation_valid"] = citation_valid
        parsed["addresses_question"] = addresses_question
        parsed["passed"] = citation_valid and addresses_question
        if not citation_required:
            parsed["passed"] = addresses_question
            parsed["citation_valid"] = True
        return parsed
    except Exception as exc:
        logger.warning("Agent verification call failed; using deterministic check: %s", exc)
        return local


def _run_model_loop(client: Any, messages: list[dict[str, Any]], user_message: str, video_id: str, db: Session, session_id: str, events: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]], int]:
    tool_results: list[dict[str, Any]] = []
    calls = 0
    model_name = get_llm_model()
    for step in range(1, MAX_STEPS + 1):
        response = client.chat.complete(
            model=model_name,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.05,
        )
        message = response.choices[0].message
        calls_for_step = [_tool_call_dict(call) for call in (message.tool_calls or [])]
        events.append({"event": "model", "step": step, "tool_calls": [call["function"]["name"] for call in calls_for_step], "timestamp": _now()})
        if not calls_for_step:
            return _content(message.content) or INSUFFICIENT_EVIDENCE, tool_results, calls

        messages.append({"role": "assistant", "content": _content(message.content), "tool_calls": calls_for_step})
        for call in calls_for_step:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
            except (TypeError, json.JSONDecodeError):
                args = {}
            try:
                result = _jsonable(_execute_tool(name, args, user_message, video_id, db, session_id))
            except Exception as exc:
                logger.exception("Agent tool %s failed", name)
                result = {"error": str(exc)}
            calls += 1
            record = {"tool": name, "arguments": args, "result": result}
            tool_results.append(record)
            events.append({"event": "tool", "step": step, **record, "timestamp": _now()})
            messages.append({
                "role": "tool",
                "name": name,
                "tool_call_id": call["id"],
                "content": json.dumps(result, ensure_ascii=False),
            })
    events.append({"event": "max_steps", "step": MAX_STEPS, "timestamp": _now()})
    return INSUFFICIENT_EVIDENCE, tool_results, calls


def _offline_loop(user_message: str, video_id: str, db: Session, session_id: str, events: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]], int]:
    lowered = user_message.lower()
    if any(word in lowered for word in ["dub", "voiceover", "audio in", "dubbing", "audio track", "generate audio"]):
        name, args = "translate_dub", {"language": "fr" if "french" in lowered or "français" in lowered else "en", "voice_gender": "female"}
    elif any(word in lowered for word in ["find", "search", "where", "show me", "locate", "timestamp"]):
        name, args = "search_video", {"query": user_message}
    else:
        name, args = "ask_question", {"question": user_message}
    try:
        result = _jsonable(_execute_tool(name, args, user_message, video_id, db, session_id))
    except Exception as exc:
        logger.warning("Offline agent tool %s failed: %s", name, exc)
        result = {"error": str(exc)}
    events.append({"event": "tool", "step": 1, "tool": name, "arguments": args, "result": result, "timestamp": _now(), "offline": True})
    if name == "ask_question":
        answer = result.get("answer", INSUFFICIENT_EVIDENCE)
    elif name == "search_video":
        moments = result.get("results", [])
        answer = (f"I found {len(moments)} relevant moments, starting at [{int(moments[0]['start_time'] // 60):02d}:{int(moments[0]['start_time'] % 60):02d}]." if moments else INSUFFICIENT_EVIDENCE)
    elif "error" not in result:
        answer = f"The {result['language'].upper()} dubbing track is ready."
    else:
        answer = INSUFFICIENT_EVIDENCE
    return answer, [{"tool": name, "arguments": args, "result": result}], 1


def _response(answer: str, tool_results: list[dict[str, Any]], session_id: str, trajectory_id: str, calls: int, verification: dict[str, Any], degraded: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": "chat",
        "content": answer,
        "answer": answer,
        "session_id": session_id,
        "mode": "loop",
        "tool_call_count": calls,
        "steps": min(MAX_STEPS, max(1, calls)),
        "verified": bool(verification.get("passed")),
        "degraded": degraded,
        "trajectory_id": trajectory_id,
        "model_used": get_llm_model(),
        "provider_used": get_llm_provider(),
    }
    for item in tool_results:
        result = item["result"]
        if item["tool"] == "search_video":
            payload.update(type="search", results=result.get("results", []))
        elif item["tool"] == "ask_question":
            payload.update(type="qa", question=result.get("question"), sources=result.get("sources", []))
        elif item["tool"] == "translate_dub" and "error" not in result:
            payload.update(type="dubbing", status="completed", language=result["language"], voice_gender=result["voice_gender"], dub_track=result["dub_track"])
    return payload


def run_agent_loop(user_message: str, video_id: str, db: Session, session_id: str = "default-session") -> dict[str, Any]:
    """Run at most MAX_STEPS per attempt and retry once after failed verification."""
    request_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}_{uuid.uuid4().hex[:8]}"
    events: list[dict[str, Any]] = [{"event": "request", "question": user_message, "video_id": video_id, "session_id": session_id, "timestamp": _now()}]
    client = get_mistral_client()
    degraded = not bool(client)
    history = _history(video_id, session_id)
    system = {"role": "system", "content": "You are Coumba, an encouraging multilingual educational tutor for Open VidLib. Use tools to find relevant lesson evidence. Answer in the language requested by the learner (including Wolof [wo], Pulaar/Fulfulde [ff], Bambara [bm], French, or English). Base lesson claims only on tool evidence. When evidence includes a 'sentences' array with per-sentence timestamps, cite the specific sentence's start time as [MM:SS] for the fact you reference — do NOT cite the overall chunk start_time. If no sentences array is present, cite the chunk's start_time. Never invent timestamps. Finish with a concise, helpful explanation in the requested language."}
    messages: list[dict[str, Any]] = [system, *history, {"role": "user", "content": user_message}]

    if client:
        try:
            answer, tool_results, calls = _run_model_loop(client, messages, user_message, video_id, db, session_id, events)
        except Exception as exc:
            logger.warning("Agent model loop unavailable; using bounded offline fallback: %s", exc)
            events.append({"event": "model_error", "error": str(exc), "timestamp": _now()})
            answer, tool_results, calls = _offline_loop(user_message, video_id, db, session_id, events)
            client = None
            degraded = True
    else:
        answer, tool_results, calls = _offline_loop(user_message, video_id, db, session_id, events)

    evidence_times = _evidence_times(tool_results)
    citation_required = any(item["tool"] in {"search_video", "ask_question"} for item in tool_results)
    verification = _verify(client, user_message, answer, evidence_times, citation_required)
    events.append({"event": "verification", "attempt": 1, "result": verification, "timestamp": _now()})

    if not verification.get("passed") and client:
        retry_messages = [system, *history, {"role": "user", "content": user_message}, {"role": "user", "content": f"Verification failed: {verification.get('feedback', '')} Retry from scratch and use tools to produce a grounded final answer."}]
        try:
            retry_answer, retry_results, retry_calls = _run_model_loop(client, retry_messages, user_message, video_id, db, session_id, events)
            retry_verification = _verify(client, user_message, retry_answer, _evidence_times(retry_results), any(item["tool"] in {"search_video", "ask_question"} for item in retry_results))
            events.append({"event": "verification", "attempt": 2, "result": retry_verification, "timestamp": _now()})
            answer, tool_results, calls, verification = retry_answer, retry_results, calls + retry_calls, retry_verification
        except Exception as exc:
            degraded = True
            verification = {"passed": False, "citation_valid": False, "addresses_question": False, "feedback": "Verification retry failed."}
            events.append({"event": "retry_error", "error": str(exc), "timestamp": _now()})

    if not verification.get("passed"):
        answer = INSUFFICIENT_EVIDENCE
    _remember(video_id, session_id, user_message, answer)
    events.append({"event": "response", "answer": answer, "tool_call_count": calls, "verified": bool(verification.get("passed")), "timestamp": _now()})

    trajectory = {"request_id": request_id, "max_steps_per_attempt": MAX_STEPS, "events": events}
    try:
        TRAJECTORY_DIR.mkdir(parents=True, exist_ok=True)
        path = TRAJECTORY_DIR / f"{request_id}.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(trajectory, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)
    except OSError as exc:
        logger.error("Could not persist agent trajectory %s: %s", request_id, exc)

    return _response(answer, tool_results, session_id, request_id, calls, verification, degraded)
