"""QR code generator for embedding original chat links into PDF cover pages."""

import base64
import io

import qrcode
from qrcode.constants import ERROR_CORRECT_M


def generate_qr_data_uri(url: str) -> str:
    """Generate a base64-encoded PNG Data URI for a given URL string.

    Encodes the exact target URL as a clean black-and-white QR code image
    suitable for HTML embedding. Returns an empty string if the URL is empty or invalid.
    """
    clean_url = (url or "").strip()
    if not clean_url:
        return ""

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(clean_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return ""
