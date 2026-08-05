"""
Utility functions for volunteer identification cards, QR codes, and reporting formats.
"""

import base64
from io import BytesIO

import qrcode  # type: ignore[import-untyped]


def generate_qr_code_base64(data: str) -> str:
    """Generate a PNG data URI for a volunteer verification QR code."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"
