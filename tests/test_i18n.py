from app.i18n import get_translator, is_rtl, normalize_language


def test_normalize_language_falls_back_to_english() -> None:
    assert normalize_language("de") == "en"
    assert normalize_language(None) == "en"
    assert normalize_language("fa") == "fa"


def test_translator_returns_persian_translation() -> None:
    translate = get_translator("fa")
    assert translate("nav.home") == "خانه"


def test_translator_falls_back_to_english_for_missing_key() -> None:
    translate = get_translator("fa")
    assert translate("nonexistent.key") == "nonexistent.key"


def test_is_rtl() -> None:
    assert is_rtl("fa") is True
    assert is_rtl("en") is False
