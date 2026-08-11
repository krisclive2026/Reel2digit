import io
import base64
import os
from urllib.parse import quote

import qrcode

# Your UPI ID (VPA) that payments should land in, e.g. "yourname@okhdfcbank".
# Set the real value in .env — this placeholder will not receive real money.
UPI_VPA = os.getenv("UPI_VPA", "your-upi-id@bank")
UPI_PAYEE_NAME = os.getenv("UPI_PAYEE_NAME", "ReelToDigit")


def build_upi_link(amount: float, note: str) -> str:
    """
    Builds a standard UPI deep link (upi://pay?...). Any UPI app — Google Pay,
    PhonePe, Paytm, BHIM, etc. — understands this scheme directly. No payment
    gateway or fees involved; money goes straight to UPI_VPA.
    """
    return (
        f"upi://pay?pa={quote(UPI_VPA)}&pn={quote(UPI_PAYEE_NAME)}"
        f"&am={amount:.2f}&cu=INR&tn={quote(note)}"
    )


def generate_qr_base64(data: str) -> str:
    """Renders a QR code for `data` and returns it as a base64 PNG string,
    ready to drop into an <img src="data:image/png;base64,..."> tag."""
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
