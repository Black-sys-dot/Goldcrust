"""Razorpay test-mode orders and payment checks.

The key id may be shown to the browser. The secret stays in this process.
Confirmation requires Razorpay's checkout signature and a matching payment
fetched from Razorpay, so a tapped "I paid" button cannot confirm an order.
"""

import os
import csv
import hashlib
import hmac
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEY_FILE = ROOT / "rzp-key.csv"
API = "https://api.razorpay.com/v1"


class PaymentError(Exception):
    pass


def load_keys():
    key_id = os.environ.get("RZP_KEY_ID", "").strip()
    secret = os.environ.get("RZP_KEY_SECRET", "").strip()
    if not key_id or not secret:
        if not KEY_FILE.exists():
            raise PaymentError("Razorpay keys are missing. Add rzp-key.csv or set RZP_KEY_ID and RZP_KEY_SECRET.")
        with KEY_FILE.open(newline="", encoding="utf-8-sig") as handle:
            row = next(csv.DictReader(handle), None)
        if not row:
            raise PaymentError("Razorpay key file is empty.")
        key_id = (row.get("key_id") or "").strip()
        secret = (row.get("key_secret") or "").strip()
    if not key_id.startswith("rzp_test_"):
        raise PaymentError("Only Razorpay test keys are accepted in this demo.")
    if not secret:
        raise PaymentError("Razorpay key secret is missing.")
    return key_id, secret


def _request(method, path, payload=None):
    key_id, secret = load_keys()
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "User-Agent": "goldcrust-demo"},
    )
    token = f"{key_id}:{secret}".encode()
    import base64
    req.add_header("Authorization", "Basic " + base64.b64encode(token).decode())
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        try:
            message = json.loads(body)["error"]["description"]
        except (json.JSONDecodeError, KeyError, TypeError):
            message = "Razorpay rejected the request."
        raise PaymentError(message) from exc
    except urllib.error.URLError as exc:
        raise PaymentError("Could not reach Razorpay.") from exc


def create_order(receipt, amount_rupees):
    created = _request("POST", "/orders", {
        "amount": int(amount_rupees) * 100,
        "currency": "INR",
        "receipt": receipt[:40],
        "payment_capture": 1,
        "notes": {"order_id": receipt},
    })
    if not created.get("id"):
        raise PaymentError("Razorpay did not return an order id.")
    return created


def fetch_payment(payment_id):
    if not payment_id or not str(payment_id).startswith("pay_"):
        raise PaymentError("Missing Razorpay payment id.")
    return _request("GET", "/payments/" + payment_id)


def signature_ok(order_id, payment_id, signature):
    _key_id, secret = load_keys()
    if not signature:
        return False
    digest = hmac.new(
        secret.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, signature)


def webhook_ok(body: bytes, signature: str, webhook_secret: str):
    if not signature or not webhook_secret:
        return False
    digest = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)
