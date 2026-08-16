from typing import Dict

# Preset voice IDs returned by the configured Mistral account.
# Mistral requires real preset/custom voice IDs; language names such as
# "fr_female" are not valid API voice IDs.
VOICE_PRESETS: Dict[str, Dict[str, str]] = {
    "en": {
        "female": "c69964a6-ab8b-4f8a-9465-ec0925096ec8",  # Paul - Neutral
        "male": "c69964a6-ab8b-4f8a-9465-ec0925096ec8",
    },
    "fr": {
        "female": "5a271406-039d-46fe-835b-fbbb00eaf08d",  # Marie - Neutral
        "male": "5a271406-039d-46fe-835b-fbbb00eaf08d",
    },
}


def get_voice_id(lang: str, gender: str = "female") -> str:
    lang_lower = lang.lower() if lang else "en"
    gender_lower = gender.lower() if gender else "female"
    return VOICE_PRESETS.get(lang_lower, VOICE_PRESETS["en"]).get(
        gender_lower, VOICE_PRESETS["en"]["female"]
    )
