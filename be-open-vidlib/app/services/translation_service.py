import logging
from app.core.config import settings
from app.core.llm_client import get_llm_client, get_llm_model, get_mistral_client, LLM_MODEL

logger = logging.getLogger(__name__)

def translate_segment(text: str, target_lang: str) -> str:
    """Translate transcript chunk optimized for spoken voiceover audio."""
    client = get_mistral_client()
    if not client:
        # Fallback if no API key
        return f"[{target_lang.upper()}] {text}"

    prompt = f"""Translate this video transcript to {target_lang}.
Rules:
- Keep it natural for spoken voiceover audio.
- Convert numbers to words (e.g., "1234" -> "one thousand two hundred thirty-four").
- Spell out abbreviations clearly.
- Do NOT use markdown, emojis, or special characters.
- Do not add explanations.

Text: {text}
Translation:"""

    try:
        resp = client.chat.complete(
            model=get_llm_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"LLM translation error: {e}")
        return text
