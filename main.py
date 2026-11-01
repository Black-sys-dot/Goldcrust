import json
import os
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import auth
import db
import pay
from catalog import BRANCH_BY_ID, PricingError, branches_with_distance, point_from_pin, quote

app = FastAPI()

PAGES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/menu.html": "menu.html",
    "/checkout.html": "checkout.html",
    "/kitchen.html": "kitchen.html",
    "/tickets.html": "tickets.html",
}


@app.on_event("startup")
def startup():
    attempts = 30 if os.environ.get("DATABASE_URL") else 1
    last_error = None
    for _ in range(attempts):
        try:
            db.init()
            return
        except Exception as exc:
            last_error = exc
            time.sleep(4)
    raise last_error


def _clean(value, limit):
    text = " ".join(str(value or "").split())
    return text[:limit]


def _coords(payload):
    lat = payload.get("lat")
    lng = payload.get("lng")
    try:
        if lat is None or lng is None or lat == "" or lng == "":
            return None
        lat_f, lng_f = float(lat), float(lng)
    except (TypeError, ValueError):
        return None
    if not (-90 <= lat_f <= 90 and -180 <= lng_f <= 180):
        return None
    # Reject a pin dropped far outside the Pune demo area.
    if not (18.3 <= lat_f <= 18.8 and 73.6 <= lng_f <= 74.1):
        return None
    return lat_f, lng_f


def _resolve_branch(mode, payload):
    coords = _coords(payload)
    pin_point = point_from_pin(payload.get("pin"))
    point = coords or (pin_point and (*pin_point, ))
    if point:
        ranked = branches_with_distance(point[0], point[1])
    else:
        ranked = branches_with_distance()

    if mode == "delivery":
        if not point:
            raise PricingError("Share your location or enter a Pune PIN so we can pick the kitchen.")
        branch = ranked[0]
        return branch, point[0], point[1]

    requested = _clean(payload.get("branch_id"), 20)
    if requested:
        branch = BRANCH_BY_ID.get(requested)
        if not branch:
            raise PricingError("Choose a Goldcrust kitchen for pickup.")
        chosen = dict(branch)
    elif point:
        chosen = ranked[0]
    else:
        chosen = dict(BRANCH_BY_ID["kp"])
    lat = point[0] if point else None
    lng = point[1] if point else None
    return chosen, lat, lng


@app.get("/api/branches")
def list_branches(lat: float | None = None, lng: float | None = None, pin: str | None = None):
    point = None
    if lat is not None and lng is not None:
        point = _coords({"lat": lat, "lng": lng})
    if point is None and pin:
        found = point_from_pin(pin)
        if found:
            point = found
    if point:
        rows = branches_with_distance(point[0], point[1])
    else:
        rows = branches_with_distance()
    return {"branches": rows}


@app.post("/api/checkout")
async def checkout(request: Request):
    payload = await request.json()
    mode = payload.get("mode")
    method = payload.get("payment_method") or "razorpay"
    name = _clean(payload.get("name"), 80)
    phone = "".join(ch for ch in str(payload.get("phone") or "") if ch.isdigit())
    if phone.startswith("91") and len(phone) == 12:
        phone = phone[2:]
    address = _clean(payload.get("address"), 240)
    city = _clean(payload.get("city"), 40) or "Pune"
    pin = "".join(ch for ch in str(payload.get("pin") or "") if ch.isdigit())[:6]
    slot = payload.get("slot") if payload.get("slot") in ("now", "hour") else "now"

    if len(name) < 2:
        raise HTTPException(400, "Add your name.")
    if len(phone) != 10:
        raise HTTPException(400, "Add a 10-digit mobile number.")
    if mode == "delivery" and len(address) < 8:
        raise HTTPException(400, "Add the delivery address.")
    if method not in ("razorpay", "cod"):
        raise HTTPException(400, "Choose a payment method.")
    if method == "cod" and mode != "pickup":
        raise HTTPException(400, "Delivery orders are paid online before the kitchen sees them.")

    try:
        bill = quote(payload.get("items"), mode, payload.get("coupon"))
        branch, lat, lng = _resolve_branch(mode, {**payload, "pin": pin})
    except PricingError as exc:
        raise HTTPException(400, str(exc)) from exc

    current_user = auth.get_current_user(request)
    user_id = current_user["id"] if current_user else None

    status = "confirmed" if method == "cod" else "pending_payment"
    order = db.create_order(
        {
            "user_id": user_id,
            "status": status,
            "mode": mode,
            "payment_method": method,
            "branch_id": branch["id"],
            "customer_name": name,
            "phone": phone,
            "address": address,
            "city": city,
            "pin": pin,
            "lat": lat,
            "lng": lng,
            "slot": slot,
            "coupon": bill["coupon"],
            "subtotal": bill["subtotal"],
            "discount": bill["discount"],
            "delivery_fee": bill["delivery_fee"],
            "packaging": bill["packaging"],
            "tax": bill["tax"],
            "total": bill["total"],
            "razorpay_order_id": None,
        },
        bill["lines"],
    )

    result = {
        "success": True,
        "order_id": order["public_id"],
        "status": order["status"],
        "mode": mode,
        "payment_method": method,
        "branch": {
            "id": branch["id"],
            "name": branch["name"],
            "area": branch["area"],
            "address": branch["address"],
        },
        "bill": {
            "subtotal": bill["subtotal"],
            "discount": bill["discount"],
            "delivery_fee": bill["delivery_fee"],
            "packaging": bill["packaging"],
            "tax": bill["tax"],
            "total": bill["total"],
        },
    }

    if method == "cod":
        return result

    try:
        key_id, _secret = pay.load_keys()
        remote = pay.create_order(order["public_id"], bill["total"])
    except pay.PaymentError as exc:
        raise HTTPException(502, str(exc)) from exc

    db.attach_razorpay_order(order["public_id"], remote["id"])
    result.update({
        "key_id": key_id,
        "razorpay_order_id": remote["id"],
        "amount": remote["amount"],
        "currency": remote["currency"],
    })
    return result


@app.post("/api/payment/verify")
async def verify_payment(request: Request):
    payload = await request.json()
    rzp_order = str(payload.get("razorpay_order_id") or "")
    payment_id = str(payload.get("razorpay_payment_id") or "")
    signature = str(payload.get("razorpay_signature") or "")

    if not pay.signature_ok(rzp_order, payment_id, signature):
        raise HTTPException(400, "Payment could not be verified.")

    order = db.get_by_razorpay_order(rzp_order)
    if not order:
        raise HTTPException(404, "Order not found.")

    try:
        remote = pay.fetch_payment(payment_id)
    except pay.PaymentError as exc:
        raise HTTPException(502, str(exc)) from exc

    if remote.get("order_id") != rzp_order:
        raise HTTPException(400, "Payment does not match this order.")
    if remote.get("status") not in ("captured", "authorized"):
        raise HTTPException(400, "Payment is not complete.")

    confirmed, err = db.confirm_payment(order["public_id"], payment_id, int(remote.get("amount") or 0))
    if err:
        raise HTTPException(400, err)
    return {
        "success": True,
        "order_id": confirmed["public_id"],
        "status": confirmed["status"],
        "mode": confirmed["mode"],
        "branch": confirmed["branch"],
        "total": confirmed["total"],
    }


@app.post("/api/webhooks/razorpay")
async def razorpay_webhook(request: Request):
    """Optional live path. Needs RZP_WEBHOOK_SECRET from the Razorpay dashboard."""
    secret = os.environ.get("RZP_WEBHOOK_SECRET", "").strip()
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")
    if not secret:
        return JSONResponse({"ok": False, "error": "Webhook secret is not configured."}, status_code=501)
    if not pay.webhook_ok(body, signature, secret):
        raise HTTPException(400, "Invalid webhook signature.")

    event = json.loads(body.decode() or "{}")
    if event.get("event") not in ("payment.captured", "payment.authorized"):
        return {"ok": True}
    entity = ((event.get("payload") or {}).get("payment") or {}).get("entity") or {}
    order = db.get_by_razorpay_order(entity.get("order_id") or "")
    if not order:
        return {"ok": True}
    confirmed, err = db.confirm_payment(order["public_id"], entity.get("id") or "", int(entity.get("amount") or 0))
    if err:
        raise HTTPException(400, err)
    return {"ok": True, "order_id": confirmed["public_id"], "status": confirmed["status"]}


@app.post("/api/auth/register")
async def register(request: Request):
    payload = await request.json()
    username = str(payload.get("username") or "").strip()
    password = str(payload.get("password") or "").strip()

    if len(username) < 3 or len(username) > 30:
        raise HTTPException(400, "Username must be between 3 and 30 characters.")
    if not username.replace("_", "").isalnum():
        raise HTTPException(400, "Username can only contain letters, numbers, and underscores.")
    if len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters.")

    existing = db.get_user_by_username(username)
    if existing:
        raise HTTPException(400, "That username is already taken. Please choose another.")

    pw_hash = auth.hash_password(password)
    user = db.create_user(username, pw_hash)
    token = auth.create_session_token(user["id"], user["username"])

    response = JSONResponse({"success": True, "user": {"id": user["id"], "username": user["username"]}})
    response.set_cookie(
        key=auth.SESSION_COOKIE,
        value=token,
        max_age=auth.SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
    )
    return response


@app.post("/api/auth/login")
async def login(request: Request):
    payload = await request.json()
    username = str(payload.get("username") or "").strip()
    password = str(payload.get("password") or "").strip()

    if not username or not password:
        raise HTTPException(400, "Enter both username and password.")

    user = db.get_user_by_username(username)
    if not user or not auth.verify_password(password, user["password_hash"]):
        raise HTTPException(400, "Invalid username or password.")

    token = auth.create_session_token(user["id"], user["username"])
    response = JSONResponse({"success": True, "user": {"id": user["id"], "username": user["username"]}})
    response.set_cookie(
        key=auth.SESSION_COOKIE,
        value=token,
        max_age=auth.SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
    )
    return response


@app.post("/api/auth/logout")
def logout():
    response = JSONResponse({"success": True})
    response.delete_cookie(key=auth.SESSION_COOKIE, path="/")
    return response


@app.get("/api/auth/me")
def me(request: Request):
    current = auth.get_current_user(request)
    if not current:
        return {"logged_in": False, "user": None}
    return {"logged_in": True, "user": current}


@app.get("/api/user/tickets")
def my_tickets(request: Request):
    current = auth.get_current_user(request)
    if not current:
        raise HTTPException(401, "Please log in to view your saved tickets.")
    tickets = db.user_tickets(current["id"])
    return {"tickets": tickets}


@app.post("/api/user/sync-tickets")
async def sync_guest_tickets(request: Request):
    current = auth.get_current_user(request)
    if not current:
        raise HTTPException(401, "Please log in to sync tickets.")
    payload = await request.json()
    ticket_ids = payload.get("ticket_ids") or []
    if not isinstance(ticket_ids, list):
        raise HTTPException(400, "ticket_ids must be a list.")
    claimed = db.claim_guest_tickets(current["id"], ticket_ids)
    return {"success": True, "claimed": claimed}



@app.get("/api/orders")
def all_orders(request: Request):
    current = auth.get_current_user(request)
    if not current:
        raise HTTPException(401, "Authentication required to view system orders.")
    return {"orders": db.list_orders()}



@app.get("/api/tickets/{ticket_id}")
def ticket(ticket_id: str):
    public_id = ticket_id.strip().upper().replace(" ", "").replace("#", "")
    order = db.get_order(public_id)
    if not order or order["status"] in ("pending_payment", "failed"):
        raise HTTPException(404, "No ticket with that number.")
    return {"ticket": db.customer_ticket(order)}


@app.get("/api/kitchen/{branch_id}/orders")
def kitchen(branch_id: str):
    if branch_id not in BRANCH_BY_ID:
        raise HTTPException(404, "Unknown kitchen.")
    return {"branch": BRANCH_BY_ID[branch_id], "orders": db.kitchen_orders(branch_id)}


@app.post("/api/kitchen/{branch_id}/orders/{public_id}")
async def kitchen_update(branch_id: str, public_id: str, request: Request):
    if branch_id not in BRANCH_BY_ID:
        raise HTTPException(404, "Unknown kitchen.")
    payload = await request.json()
    updated, err = db.advance_status(public_id, branch_id, payload.get("status"))
    if err:
        raise HTTPException(400, err)
    return {"success": True, "order": updated}


def _page(name: str):
    with open(name, encoding="utf-8") as handle:
        return HTMLResponse(handle.read())


def _page_route(filename: str):
    def handler():
        return _page(filename)

    handler.__name__ = "page_" + filename.replace(".", "_")
    return handler


for path, filename in PAGES.items():
    app.add_api_route(path, _page_route(filename), methods=["GET"])


app.mount("/assets", StaticFiles(directory="assets"), name="assets")
