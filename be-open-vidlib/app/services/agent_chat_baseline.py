"""Pre-challenge baseline: the original single-shot agent router.

Keep this implementation intentionally single-shot so evaluations can compare the
new loop with the exact behavior that existed before the Frontier challenge work.
"""

import json
import logging
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.mistral_client import get_mistral_client, LLM_MODEL
from app.services.search_service import search_video
from app.services.rag_qa_service import ask_video_question
from app.services.dubbing_service import create_dubbed_track

logger = logging.getLogger(__name__)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_video",
            "description": "User wants to find a specific keyword, topic, quote, or moment in the video. Use for keywords like: find, search, where, show me, locate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query to find in the video timestamps"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_question",
            "description": "User asks a question requiring an educational synthesized answer grounded in the video content. Use for: what, why, how, explain, summarize, analogy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The question to answer"}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "translate_dub",
            "description": "Generate audio dubbing or spoken voiceover tracks for the video (available in English and French only). Do NOT use this tool for text Q&A or when a learner wants an explanation/answer in Wolof, Pulaar, Bambara, French, or English — for text tutoring, use ask_question or search_video and respond in the requested language.",
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {"type": "string", "description": "Target voiceover language code ('en' or 'fr')"},
                    "voice_gender": {"type": "string", "enum": ["female", "male"], "default": "female"}
                },
                "required": ["language"]
            }
        }
    }
]


def route_user_intent_baseline(user_message: str, video_id: str, db: Session, session_id: str = "default-session") -> dict:
    """Original single-shot behavior, preserved as the evaluation baseline."""
    client = get_mistral_client()

    if client and settings.MISTRAL_API_KEY:
        try:
            response = client.chat.complete(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": user_message}],
                tools=TOOLS,
                tool_choice="auto"
            )

            message = response.choices[0].message

            if not message.tool_calls:
                return {
                    "type": "chat",
                    "content": message.content or "How can I help you explore this video lesson today?",
                    "session_id": session_id
                }

            tool_call = message.tool_calls[0]
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else tool_call.function.arguments

            if tool_name == "search_video":
                results = search_video(video_id, args.get("query", user_message), db)
                return {
                    "type": "search",
                    "content": f"Found {len(results)} relevant moments in the video.",
                    "results": results,
                    "session_id": session_id
                }

            elif tool_name == "ask_question":
                result = ask_video_question(video_id, args.get("question", user_message), db, session_id=session_id)
                return {
                    "type": "qa",
                    "question": args.get("question", user_message),
                    "answer": result["answer"],
                    "sources": result["sources"],
                    "session_id": session_id
                }

            elif tool_name == "translate_dub":
                target_lang = args.get("language", "fr")
                voice_gender = args.get("voice_gender", "female")
                dub_result = create_dubbed_track(video_id, target_lang, voice_gender, db)
                return {
                    "type": "dubbing",
                    "status": "completed",
                    "language": target_lang,
                    "voice_gender": voice_gender,
                    "dub_track": dub_result,
                    "content": f"AI dubbing track generated for {target_lang.upper()} using {voice_gender} voice.",
                    "session_id": session_id
                }
        except Exception as e:
            logger.warning(f"Mistral agent routing error: {e}")

    msg_lower = user_message.lower()
    if any(k in msg_lower for k in ["find", "search", "where", "show me", "locate", "timestamp"]):
        results = search_video(video_id, user_message, db)
        return {
            "type": "search",
            "content": f"Found {len(results)} matching moments in the video.",
            "results": results,
            "session_id": session_id
        }
    elif any(k in msg_lower for k in ["translate", "dub", "voice", "audio in"]):
        lang = "fr" if "french" in msg_lower or "fr" in msg_lower else "en"
        dub_result = create_dubbed_track(video_id, lang, "female", db)
        return {
            "type": "dubbing",
            "status": "completed",
            "language": lang,
            "voice_gender": "female",
            "dub_track": dub_result,
            "content": f"Dubbed audio track ready in {lang.upper()}.",
            "session_id": session_id
        }
    else:
        result = ask_video_question(video_id, user_message, db, session_id=session_id)
        return {
            "type": "qa",
            "question": user_message,
            "answer": result["answer"],
            "sources": result["sources"],
            "session_id": session_id
        }
