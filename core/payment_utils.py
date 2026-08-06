import os
import razorpay
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def create_order(amount_rupees):
    """
    Create a Razorpay order. amount_rupees is a plain number like 500 (for ₹500).
    Razorpay's API requires the amount in paise (smallest currency unit), hence *100.
    """
    order = client.order.create({
        "amount": int(amount_rupees * 100),
        "currency": "INR",
        "payment_capture": 1,  # auto-capture the payment once authorized
    })
    return order


def verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """
    Verifies that a payment callback genuinely came from Razorpay, not a forged
    request from someone tampering with the frontend. Raises SignatureVerificationError
    if invalid.
    """
    params = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature,
    }
    client.utility.verify_payment_signature(params)
    return True