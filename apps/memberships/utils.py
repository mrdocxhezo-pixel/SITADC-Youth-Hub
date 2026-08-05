"""
Utility functions for membership identification cards and QR codes.
"""

import base64
from io import BytesIO


def generate_member_qr_base64(data: str) -> str:
    """
    Generate a PNG data URI string for a QR code for membership cards.
    Falls back gracefully if the qrcode library is not installed.
    """
    try:
        import qrcode  # type: ignore[import-untyped]

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=6,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
    except ImportError:
        svg = (
            '<svg width="120" height="120" xmlns="http://www.w3.org/2000/svg">'
            '<rect width="120" height="120" fill="#f0f0f0"/>'
            '<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" '
            'fill="#333" font-size="10">QR Code</text></svg>'
        )
        encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
        return f"data:image/svg+xml;base64,{encoded}"
