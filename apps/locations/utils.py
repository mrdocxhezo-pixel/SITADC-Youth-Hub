"""Utility helpers for the geographic locations module."""


def leaf_name(model):
    """Return the human-readable singular label for a hierarchy model."""
    return model._meta.verbose_name


def derive_code(candidate: str) -> str:
    """Normalise a user-supplied code into a slug-like token."""
    import unicodedata

    value = unicodedata.normalize("NFKD", candidate or "")
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.strip().upper().replace(" ", "-").replace("_", "-")
    keep = "".join(c for c in value if c.isalnum() or c == "-")
    return keep[:50]
