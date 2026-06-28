# language/loader.py
import json
import os
import logging

logger = logging.getLogger(__name__)

import json
import os
import logging

logger = logging.getLogger(__name__)
_translations_cache = {}

def load_translations(lang: str, fallback: str = "en") -> dict:
    """Carga el archivo de traducciones para el idioma especificado."""
    if lang in _translations_cache:
        return _translations_cache[lang]

    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, f"{lang}.json")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            _translations_cache[lang] = data
            return data
    except FileNotFoundError:
        logger.warning(f"Translation file for '{lang}' not found. Falling back to '{fallback}'.")
        if lang != fallback:
            return load_translations(fallback, fallback)
        logger.error("Fallback language file 'en.json' also missing.")
        return {}