import uuid


def generate_unique_reference(prefix: str = "REF") -> str:
    """
    Generates a unique reference string with an optional prefix.
    """
    unique_id = uuid.uuid4().hex[:8].upper()
    return f"{prefix}-{unique_id}"
