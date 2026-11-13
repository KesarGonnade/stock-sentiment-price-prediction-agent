
import argostranslate.translate


def translate_text(text, source_language="zh", target_language="en"):
    """Translate text locally using Argos Translate."""

    if not text or not text.strip():
        return ""

    if source_language == target_language:
        return text

    translation = argostranslate.translate.get_translation_from_codes(
        source_language,
        target_language
    )

    return translation.translate(text)


def translate_article(article):
    """Translate an article while preserving its original content."""

    language = article.get("original_language", "unknown")

    if language == "en":
        article["translated_title"] = article.get("original_title", "")
        article["translated_text"] = article.get("original_text", "")
        article["translation_status"] = "not_required"

    elif language == "zh":
        article["translated_title"] = translate_text(
            article.get("original_title", "")
        )
        article["translated_text"] = translate_text(
            article.get("original_text", "")
        )
        article["translation_status"] = "translated"

    else:
        article["translation_status"] = "unsupported_language"

    return article
