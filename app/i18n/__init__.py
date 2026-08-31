"""Lightweight JSON-backed translation catalogues.

English is the default and the fallback for any missing key. Persian is an
optional right-to-left language.
"""

import json
from collections.abc import Callable
from pathlib import Path

_LOCALES_DIR = Path(__file__).parent / "locales"

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "fa")
RTL_LANGUAGES = frozenset({"fa"})
LANGUAGE_NAMES = {"en": "English", "fa": "فارسی"}

_catalogues: dict[str, dict[str, str]] = {}


def _catalogue(language: str) -> dict[str, str]:
    if language not in _catalogues:
        path = _LOCALES_DIR / f"{language}.json"
        _catalogues[language] = json.loads(path.read_text(encoding="utf-8"))
    return _catalogues[language]


def normalize_language(language: str | None) -> str:
    """Return a supported language code, falling back to the default."""
    return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def is_rtl(language: str) -> bool:
    return language in RTL_LANGUAGES


def get_translator(language: str) -> Callable[[str], str]:
    """Return a ``translate(key)`` function for the given language."""
    catalogue = _catalogue(normalize_language(language))
    fallback = _catalogue(DEFAULT_LANGUAGE)

    def translate(key: str) -> str:
        return catalogue.get(key, fallback.get(key, key))

    return translate
