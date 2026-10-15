"""Menu prices, fees, and the Pune branch list.

Menu prices are read from assets/js/data.js so the page and the server
charge the same amount. Branches are the demo kitchen network.
"""

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

FEES = {"delivery": 39, "packaging": 20, "tax_rate": 0.05, "free_delivery_over": 599}

SIZE_CATEGORIES = {"chicken", "burgers", "sides", "combos", "drinks"}
# Spicy items outside the chicken category. Every chicken item offers spice.
EXTRA_SPICE = {"bg-01", "bg-06", "wr-02", "sd-02"}

OPTIONS = {
    "size": {
        "regular": ("Regular", 0),
        "large": ("Large", 60),
        "sharing": ("Sharing", 140),
    },
    "spice": {
        "mild": ("Mild", 0),
        "medium": ("Medium", 0),
        "hot": ("Fiery hot", 20),
    },
    "addons": {
        "cheese": ("Extra cheese slice", 35),
        "dip": ("Signature dip", 25),
        "fries": ("Upgrade to fries", 60),
        "drink": ("Add a chilled cola", 55),
    },
}

# Sixteen Goldcrust kitchens across Pune. Coordinates are the branch sites
# used to pick the closest kitchen.
BRANCHES = [
    {"id": "kp", "name": "Koregaon Park", "area": "Koregaon Park", "address": "North Main Road, Koregaon Park", "lat": 18.5362, "lng": 73.8939, "phone": "020 4000 1001"},
    {"id": "kn", "name": "Kalyani Nagar", "area": "Kalyani Nagar", "address": "East Avenue, Kalyani Nagar", "lat": 18.5481, "lng": 73.9026, "phone": "020 4000 1002"},
    {"id": "vn", "name": "Viman Nagar", "area": "Viman Nagar", "address": "Datta Mandir Road, Viman Nagar", "lat": 18.5679, "lng": 73.9143, "phone": "020 4000 1003"},
    {"id": "kh", "name": "Kharadi", "area": "Kharadi", "address": "Fountain Road, Kharadi", "lat": 18.5515, "lng": 73.9374, "phone": "020 4000 1004"},
    {"id": "mg", "name": "Magarpatta", "area": "Magarpatta", "address": "Magarpatta City, Hadapsar", "lat": 18.5158, "lng": 73.9272, "phone": "020 4000 1005"},
    {"id": "hd", "name": "Hadapsar", "area": "Hadapsar", "address": "Solapur Road, Hadapsar", "lat": 18.5018, "lng": 73.9260, "phone": "020 4000 1006"},
    {"id": "camp", "name": "Camp", "area": "Camp", "address": "MG Road, Camp", "lat": 18.5196, "lng": 73.8553, "phone": "020 4000 1007"},
    {"id": "fc", "name": "FC Road", "area": "FC Road", "address": "Fergusson College Road", "lat": 18.5285, "lng": 73.8410, "phone": "020 4000 1008"},
    {"id": "dc", "name": "Deccan", "area": "Deccan", "address": "Jangli Maharaj Road, Deccan", "lat": 18.5160, "lng": 73.8412, "phone": "020 4000 1009"},
    {"id": "kt", "name": "Kothrud", "area": "Kothrud", "address": "Karve Road, Kothrud", "lat": 18.5074, "lng": 73.8077, "phone": "020 4000 1010"},
    {"id": "au", "name": "Aundh", "area": "Aundh", "address": "DP Road, Aundh", "lat": 18.5580, "lng": 73.8075, "phone": "020 4000 1011"},
    {"id": "bn", "name": "Baner", "area": "Baner", "address": "Baner Road, Baner", "lat": 18.5590, "lng": 73.7868, "phone": "020 4000 1012"},
    {"id": "wk", "name": "Wakad", "area": "Wakad", "address": "Wakad Chowk, Wakad", "lat": 18.5998, "lng": 73.7645, "phone": "020 4000 1013"},
    {"id": "hj", "name": "Hinjewadi", "area": "Hinjewadi", "address": "Phase 1, Hinjewadi", "lat": 18.5913, "lng": 73.7389, "phone": "020 4000 1014"},
    {"id": "ps", "name": "Pimple Saudagar", "area": "Pimple Saudagar", "address": "Rahatani Road, Pimple Saudagar", "lat": 18.5972, "lng": 73.7978, "phone": "020 4000 1015"},
    {"id": "sr", "name": "Sinhagad Road", "area": "Sinhagad Road", "address": "Sinhagad Road, Dhayari", "lat": 18.4765, "lng": 73.8265, "phone": "020 4000 1016"},
]

# Approximate PIN centroids so a delivery address still picks a kitchen
# when the browser cannot share GPS.
PINS = {
    "411001": (18.5196, 73.8553),
    "411004": (18.5160, 73.8412),
    "411005": (18.5302, 73.8506),
    "411006": (18.5481, 73.8900),
    "411007": (18.5580, 73.8075),
    "411008": (18.5520, 73.8250),
    "411009": (18.4920, 73.8550),
    "411014": (18.5679, 73.9143),
    "411016": (18.5080, 73.9265),
    "411017": (18.5972, 73.7978),
    "411027": (18.6200, 73.8000),
    "411028": (18.5158, 73.9272),
    "411033": (18.4690, 73.8640),
    "411036": (18.5515, 73.9374),
    "411038": (18.5074, 73.8077),
    "411040": (18.4810, 73.9010),
    "411041": (18.4765, 73.8265),
    "411045": (18.5590, 73.7868),
    "411052": (18.4900, 73.8200),
    "411057": (18.5950, 73.7520),
}

BRANCH_BY_ID = {b["id"]: b for b in BRANCHES}


class PricingError(ValueError):
    pass


def load_menu():
    text = (ROOT / "assets" / "js" / "data.js").read_text(encoding="utf-8")
    start = text.index("const MENU = [")
    end = text.index("const OPTION_GROUPS")
    items = {}
    for part in re.split(r"\n  \{", text[start:end]):
        id_match = re.search(r"id:\s*'([^']+)'", part)
        name_match = re.search(r"name:\s*'((?:\\'|[^'])*)'", part)
        cat_match = re.search(r"category:\s*'([^']+)'", part)
        price_match = re.search(r"price:\s*(\d+)", part)
        if not (id_match and name_match and cat_match and price_match):
            continue
        emoji_match = re.search(r"emoji:\s*'([^']*)'", part)
        tag_match = re.search(r"tags:\s*\[([^\]]*)\]", part)
        tags = re.findall(r"'([^']+)'", tag_match.group(1)) if tag_match else []
        items[id_match.group(1)] = {
            "id": id_match.group(1),
            "name": name_match.group(1).replace("\\'", "'"),
            "category": cat_match.group(1),
            "emoji": emoji_match.group(1) if emoji_match else "",
            "price": int(price_match.group(1)),
            "tags": tags,
        }
    if len(items) < 30:
        raise RuntimeError(f"Menu parse failed, found {len(items)} items")
    return items


MENU = load_menu()


def distance_km(lat1, lng1, lat2, lng2):
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def point_from_pin(pin):
    digits = re.sub(r"\D", "", pin or "")
    return PINS.get(digits)


def branches_with_distance(lat=None, lng=None):
    rows = []
    for branch in BRANCHES:
        row = dict(branch)
        if lat is not None and lng is not None:
            row["distance_km"] = round(distance_km(lat, lng, branch["lat"], branch["lng"]), 1)
        rows.append(row)
    if lat is not None and lng is not None:
        rows.sort(key=lambda row: row["distance_km"])
        if rows:
            rows[0]["nearest"] = True
    return rows


def _groups_for(item):
    groups = []
    if item["category"] in SIZE_CATEGORIES:
        groups.append("size")
    if item["category"] == "chicken" or "spicy" in item["tags"] or item["id"] in EXTRA_SPICE:
        groups.append("spice")
    groups.append("addons")
    return groups


def price_items(raw_items):
    """Return priced line dicts and the item subtotal. Raises PricingError."""
    if not isinstance(raw_items, list) or not raw_items:
        raise PricingError("Add at least one item.")
    if len(raw_items) > 30:
        raise PricingError("Too many lines in one order.")

    lines = []
    subtotal = 0
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise PricingError("Invalid item.")
        item = MENU.get(str(raw.get("id") or ""))
        if not item:
            raise PricingError("One of the items is no longer on the menu.")
        try:
            qty = int(raw.get("qty") or 0)
        except (TypeError, ValueError):
            raise PricingError("Invalid quantity.")
        if qty < 1 or qty > 20:
            raise PricingError("Quantity must be between 1 and 20.")

        choices = raw.get("choices") or {}
        addons = raw.get("addons") or []
        if not isinstance(choices, dict) or not isinstance(addons, list):
            raise PricingError("Invalid options.")

        allowed = _groups_for(item)
        unit = item["price"]
        parts = []

        for group in ("size", "spice"):
            if group not in allowed:
                if choices.get(group):
                    raise PricingError(f"{item['name']} does not take that option.")
                continue
            choice_id = choices.get(group) or next(iter(OPTIONS[group]))
            picked = OPTIONS[group].get(choice_id)
            if not picked:
                raise PricingError(f"Unknown option on {item['name']}.")
            unit += picked[1]
            parts.append(picked[0])

        seen = set()
        for addon_id in addons:
            if addon_id in seen:
                continue
            seen.add(addon_id)
            picked = OPTIONS["addons"].get(addon_id)
            if not picked:
                raise PricingError(f"Unknown extra on {item['name']}.")
            unit += picked[1]
            parts.append(picked[0])

        line_total = unit * qty
        subtotal += line_total
        lines.append({
            "item_id": item["id"],
            "name": item["name"],
            "emoji": item["emoji"],
            "qty": qty,
            "unit_price": unit,
            "option_text": " · ".join(parts) or "Regular",
        })
    return lines, subtotal


def quote(raw_items, mode, coupon):
    """Full bill. Pickup has no delivery fee. Coupon rules match the checkout page."""
    lines, subtotal = price_items(raw_items)
    if mode not in ("delivery", "pickup"):
        raise PricingError("Choose delivery or pickup.")

    delivery = 0
    if mode == "delivery" and subtotal < FEES["free_delivery_over"]:
        delivery = FEES["delivery"]
    packaging = FEES["packaging"] if subtotal else 0
    tax = round(subtotal * FEES["tax_rate"])

    code = (coupon or "").strip().upper()
    discount = 0
    if code == "CRUST50":
        discount = min(120, round(subtotal * 0.5))
    elif code == "BUCKET99":
        if subtotal < 599:
            raise PricingError("BUCKET99 needs a minimum order of ₹599.")
        discount = 99
    elif code == "FREEDEL":
        discount = delivery
    elif code:
        raise PricingError("That code is not valid right now.")

    total = max(0, subtotal + delivery + packaging + tax - discount)
    if total < 1:
        raise PricingError("Order total must be at least ₹1.")
    return {
        "lines": lines,
        "subtotal": subtotal,
        "discount": discount,
        "delivery_fee": delivery,
        "packaging": packaging,
        "tax": tax,
        "total": total,
        "coupon": code,
    }
