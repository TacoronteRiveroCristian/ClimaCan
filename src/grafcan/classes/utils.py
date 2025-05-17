import unidecode


def normalize_variable_name(text: str) -> str:
    """Normalizes a text string for use as a variable name."""
    if text is None:
        return ""  # Or raise an error, depending on desired behavior
    # Ensure text is a string before applying unidecode
    normalized_text = unidecode.unidecode(str(text))
    normalized_text = normalized_text.replace("ñ", "n").replace("Ñ", "N")
    normalized_text = normalized_text.replace(" ", "_")
    normalized_text = normalized_text.replace(",", "")
    normalized_text = normalized_text.lower()
    normalized_text = normalized_text.replace("(", "")
    normalized_text = normalized_text.replace(")", "")
    return normalized_text
