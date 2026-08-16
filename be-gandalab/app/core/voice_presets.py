from typing import Dict

VOICE_PRESETS: Dict[str, Dict[str, str]] = {
    "en": {
        "female": "neutral_female",
        "male": "neutral_male",
        "casual_f": "casual_female",
        "casual_m": "casual_male",
        "cheerful": "cheerful_female"
    },
    "fr": {
        "female": "fr_female",
        "male": "fr_male"
    },
    "es": {
        "female": "es_female",
        "male": "es_male"
    },
    "de": {
        "female": "de_female",
        "male": "de_male"
    },
    "it": {
        "female": "it_female",
        "male": "it_male"
    },
    "pt": {
        "female": "pt_female",
        "male": "pt_male"
    },
    "nl": {
        "female": "nl_female",
        "male": "nl_male"
    },
    "hi": {
        "female": "hi_female",
        "male": "hi_male"
    },
    "ar": {
        "female": "ar_female",
        "male": "ar_male"
    },
    "wo": {
        "female": "neutral_female",
        "male": "neutral_male"
    },
    "ff": {
        "female": "neutral_female",
        "male": "neutral_male"
    },
    "bm": {
        "female": "neutral_female",
        "male": "neutral_male"
    }
}

def get_voice_id(lang: str, gender: str = "female") -> str:
    lang_lower = lang.lower() if lang else "en"
    gender_lower = gender.lower() if gender else "female"
    return VOICE_PRESETS.get(lang_lower, {}).get(gender_lower, "neutral_female")
