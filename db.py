"""Orders and branches.

Locally this is a SQLite file. On AWS, set DATABASE_URL to the Postgres
connection string and the same tables are created there.
"""

import os
import re
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from catalog import BRANCHES

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "goldcrust.db"
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
_lock = Lock()

NEXT_STATUS = {
    "confirmed": "preparing",
    "preparing": "ready",
    "ready": "completed",
}


class _Conn:
    """One execute() surface for SQLite (?) and Postgres (%s / %(name)s)."""

    def __init__(self, raw, postgres):
        self.raw = raw
        self.postgres = postgres

    def _sql(self, sql):
        if not self.postgres:
            return sql
        sql = re.sub(r"(?<!:):([A-Za-z_][A-Za-z0-9_]*)", r"%(\1)s", sql)
        return sql.replace("?", "%s")

    def execute(self, sql, params=None):
        if params is None:
            return self.raw.execute(self._sql(sql))
        return self.raw.execute(self._sql(sql), params)

    def executemany(self, sql, seq):
        sql = self._sql(sql)
        rows = list(seq)
        if not self.postgres:
            return self.raw.executemany(sql, rows)
        # psycopg connections have execute(), not executemany().
        with self.raw.cursor() as cur:
            for row in rows:
                cur.execute(sql, row)

    def executescript(self, script):
        if not self.postgres:
            self.raw.executescript(script)
            return
        for statement in script.split(";"):
            if statement.strip():
                self.raw.execute(statement)

    def commit(self):
        self.raw.commit()

    def rollback(self):
        self.raw.rollback()

    def close(self):
        self.raw.close()


def _connect():
    if DATABASE_URL:
        import psycopg
        from psycopg.rows import dict_row
        raw = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        return _Conn(raw, True)
    DB_PATH.parent.mkdir(exist_ok=True)
    raw = sqlite3.connect(DB_PATH, check_same_thread=False)
    raw.row_factory = sqlite3.Row
    raw.execute("PRAGMA foreign_keys = ON")
    return _Conn(raw, False)


def init():
    with _lock:
        conn = _connect()
        try:
            script = """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    default_name TEXT,
                    default_phone TEXT,
                    default_address TEXT,
                    default_city TEXT,
                    default_pin TEXT
                );

                CREATE TABLE IF NOT EXISTS branches (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    area TEXT NOT NULL,
                    address TEXT NOT NULL,
                    lat REAL NOT NULL,
                    lng REAL NOT NULL,
                    phone TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    public_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER REFERENCES users(id),
                    status TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    payment_method TEXT NOT NULL,
                    branch_id TEXT NOT NULL,
                    customer_name TEXT NOT NULL,
                    phone TEXT,
                    address TEXT,
                    city TEXT,
                    pin TEXT,
                    lat REAL,
                    lng REAL,
                    slot TEXT,
                    coupon TEXT,
                    subtotal INTEGER NOT NULL,
                    discount INTEGER NOT NULL,
                    delivery_fee INTEGER NOT NULL,
                    packaging INTEGER NOT NULL,
                    tax INTEGER NOT NULL,
                    total INTEGER NOT NULL,
                    razorpay_order_id TEXT,
                    razorpay_payment_id TEXT,
                    created_at TEXT NOT NULL,
                    confirmed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL REFERENCES orders(id),
                    item_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    emoji TEXT,
                    qty INTEGER NOT NULL,
                    unit_price INTEGER NOT NULL,
                    option_text TEXT
                );
            """
            if DATABASE_URL:
                script = script.replace(
                    "id INTEGER PRIMARY KEY AUTOINCREMENT",
                    "id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY",
                ).replace(
                    "user_id INTEGER REFERENCES users(id)",
                    "user_id BIGINT REFERENCES users(id)",
                )
            conn.executescript(script)
            # Ensure user_id exists if the orders table was already created
            if DATABASE_URL:
                conn.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS user_id BIGINT REFERENCES users(id)")
                conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS default_name TEXT")
                conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS default_phone TEXT")
                conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS default_address TEXT")
                conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS default_city TEXT")
                conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS default_pin TEXT")
            else:
                cols = [r["name"] for r in conn.execute("PRAGMA table_info(orders)").fetchall()]
                if "user_id" not in cols:
                    conn.execute("ALTER TABLE orders ADD COLUMN user_id INTEGER REFERENCES users(id)")
                u_cols = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
                for col in ("default_name", "default_phone", "default_address", "default_city", "default_pin"):
                    if col not in u_cols:
                        conn.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
            for branch in BRANCHES:
                conn.execute(
                    """
                    INSERT INTO branches (id, name, area, address, lat, lng, phone)
                    VALUES (:id, :name, :area, :address, :lat, :lng, :phone)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        area = excluded.area,
                        address = excluded.address,
                        lat = excluded.lat,
                        lng = excluded.lng,
                        phone = excluded.phone
                    """,
                    branch,
                )
            conn.commit()
        finally:
            conn.close()


def _now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _items_for(conn, order_id):
    rows = conn.execute(
        "SELECT item_id, name, emoji, qty, unit_price, option_text FROM order_items WHERE order_id = ? ORDER BY id",
        (order_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _branch(conn, branch_id):
    row = conn.execute("SELECT * FROM branches WHERE id = ?", (branch_id,)).fetchone()
    return dict(row) if row else None


def _public(order_row, conn):
    data = dict(order_row)
    data["items"] = _items_for(conn, data["id"])
    data["branch"] = _branch(conn, data["branch_id"])
    data.pop("id", None)
    return data


def customer_ticket(order):
    """The copy a customer can hold. Payment secrets stay off it."""
    branch = order.get("branch") or {}
    return {
        "ticket": order["public_id"],
        "status": order["status"],
        "mode": order["mode"],
        "payment_method": order["payment_method"],
        "name": order["customer_name"],
        "slot": order["slot"],
        "total": order["total"],
        "created_at": order["created_at"],
        "address": order["address"] if order["mode"] == "delivery" else "",
        "branch": {
            "id": branch.get("id"),
            "name": branch.get("name"),
            "address": branch.get("address"),
        },
        "items": [
            {
                "name": item["name"],
                "emoji": item["emoji"],
                "qty": item["qty"],
                "option_text": item["option_text"],
            }
            for item in order["items"]
        ],
    }


TICKET_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def generate_ticket_id(conn) -> str:
    """Generate a random, non-sequential Crockford base32 ticket identifier."""
    for _ in range(30):
        code = "".join(secrets.choice(TICKET_ALPHABET) for _ in range(6))
        candidate = f"GC{code}"
        row = conn.execute("SELECT 1 FROM orders WHERE public_id = ?", (candidate,)).fetchone()
        if not row:
            return candidate
    return f"GC{uuid.uuid4().hex[:6].upper()}"


def create_order(header, lines):
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute(
                """
                INSERT INTO orders (
                    public_id, user_id, status, mode, payment_method, branch_id,
                    customer_name, phone, address, city, pin, lat, lng, slot, coupon,
                    subtotal, discount, delivery_fee, packaging, tax, total,
                    razorpay_order_id, created_at
                ) VALUES (
                    :public_id, :user_id, :status, :mode, :payment_method, :branch_id,
                    :customer_name, :phone, :address, :city, :pin, :lat, :lng, :slot, :coupon,
                    :subtotal, :discount, :delivery_fee, :packaging, :tax, :total,
                    :razorpay_order_id, :created_at
                )
                RETURNING id
                """,
                {
                    **header,
                    "user_id": header.get("user_id"),
                    "public_id": "tmp-" + uuid.uuid4().hex,
                    "created_at": _now(),
                },
            )
            order_id = cur.fetchone()["id"]
            public_id = generate_ticket_id(conn)
            conn.execute("UPDATE orders SET public_id = ? WHERE id = ?", (public_id, order_id))
            conn.executemany(
                """
                INSERT INTO order_items (order_id, item_id, name, emoji, qty, unit_price, option_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (order_id, line["item_id"], line["name"], line["emoji"], line["qty"], line["unit_price"], line["option_text"])
                    for line in lines
                ],
            )
            if header.get("status") == "confirmed":
                conn.execute("UPDATE orders SET confirmed_at = ? WHERE id = ?", (_now(), order_id))
            conn.commit()
            row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            return _public(row, conn)
        finally:
            conn.close()


def attach_razorpay_order(public_id, razorpay_order_id):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "UPDATE orders SET razorpay_order_id = ? WHERE public_id = ?",
                (razorpay_order_id, public_id),
            )
            conn.commit()
        finally:
            conn.close()


def get_order(public_id):
    conn = _connect()
    try:
        clean = str(public_id or "").strip().upper().replace(" ", "").replace("#", "").replace("-", "")
        row = conn.execute(
            "SELECT * FROM orders WHERE public_id = ? OR REPLACE(public_id, '-', '') = ?",
            (public_id, clean),
        ).fetchone()
        return _public(row, conn) if row else None
    finally:
        conn.close()


def get_by_razorpay_order(razorpay_order_id):
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM orders WHERE razorpay_order_id = ?",
            (razorpay_order_id,),
        ).fetchone()
        return _public(row, conn) if row else None
    finally:
        conn.close()


def confirm_payment(public_id, payment_id, expected_paise):
    """Mark a pending order confirmed. Safe to call twice for the same payment."""
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT * FROM orders WHERE public_id = ?", (public_id,)).fetchone()
            if not row:
                return None, "Order not found."
            if row["total"] * 100 != expected_paise:
                return None, "Payment amount does not match the order."
            if row["status"] != "pending_payment":
                if row["razorpay_payment_id"] == payment_id or row["status"] in NEXT_STATUS or row["status"] == "completed":
                    return _public(row, conn), None
                return None, "This order can no longer be paid."
            conn.execute(
                """
                UPDATE orders
                SET status = 'confirmed', razorpay_payment_id = ?, confirmed_at = ?
                WHERE public_id = ? AND status = 'pending_payment'
                """,
                (payment_id, _now(), public_id),
            )
            conn.commit()
            fresh = conn.execute("SELECT * FROM orders WHERE public_id = ?", (public_id,)).fetchone()
            return _public(fresh, conn), None
        finally:
            conn.close()


def kitchen_orders(branch_id):
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT * FROM orders
            WHERE branch_id = ? AND status != 'pending_payment' AND status != 'failed'
            ORDER BY created_at DESC
            """,
            (branch_id,),
        ).fetchall()
        return [_public(row, conn) for row in rows]
    finally:
        conn.close()


def advance_status(public_id, branch_id, target):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT * FROM orders WHERE public_id = ?", (public_id,)).fetchone()
            if not row or row["branch_id"] != branch_id:
                return None, "Order not found at this kitchen."
            expected = NEXT_STATUS.get(row["status"])
            if target != expected:
                return None, "That status change is not available."
            conn.execute(
                "UPDATE orders SET status = ? WHERE public_id = ?",
                (target, public_id),
            )
            conn.commit()
            fresh = conn.execute("SELECT * FROM orders WHERE public_id = ?", (public_id,)).fetchone()
            return _public(fresh, conn), None
        finally:
            conn.close()


def list_orders():
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        return [_public(row, conn) for row in rows]
    finally:
        conn.close()


def create_user(username: str, password_hash: str):
    with _lock:
        conn = _connect()
        try:
            created = _now()
            cur = conn.execute(
                """
                INSERT INTO users (username, password_hash, created_at)
                VALUES (?, ?, ?)
                RETURNING id, username, created_at
                """,
                (username.strip(), password_hash, created),
            )
            row = cur.fetchone()
            conn.commit()
            return dict(row)
        finally:
            conn.close()


def get_user_by_username(username: str):
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE lower(username) = lower(?)",
            (username.strip(),),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: int):
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT id, username, created_at,
                   default_name, default_phone, default_address, default_city, default_pin
            FROM users WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["saved_info"] = {
            "name": d.pop("default_name", None) or "",
            "phone": d.pop("default_phone", None) or "",
            "address": d.pop("default_address", None) or "",
            "city": d.pop("default_city", None) or "",
            "pin": d.pop("default_pin", None) or "",
        }
        return d
    finally:
        conn.close()


def update_user_saved_info(user_id: int, info: dict):
    with _lock:
        conn = _connect()
        try:
            name = str(info.get("name") or "").strip()[:80]
            phone = "".join(ch for ch in str(info.get("phone") or "") if ch.isdigit())[:15]
            address = str(info.get("address") or "").strip()[:240]
            city = str(info.get("city") or "").strip()[:40]
            pin = "".join(ch for ch in str(info.get("pin") or "") if ch.isdigit())[:6]

            conn.execute(
                """
                UPDATE users
                SET default_name = ?, default_phone = ?, default_address = ?, default_city = ?, default_pin = ?
                WHERE id = ?
                """,
                (name, phone, address, city, pin, user_id),
            )
            conn.commit()
            return {
                "name": name,
                "phone": phone,
                "address": address,
                "city": city,
                "pin": pin,
            }
        finally:
            conn.close()


def user_tickets(user_id: int):
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT * FROM orders
            WHERE user_id = ? AND status != 'pending_payment' AND status != 'failed'
            ORDER BY id DESC
            """,
            (user_id,),
        ).fetchall()
        return [customer_ticket(_public(row, conn)) for row in rows]
    finally:
        conn.close()


def claim_guest_tickets(user_id: int, ticket_ids: list[str]) -> list[str]:
    """Link any unassigned (guest) tickets to the logged-in user.

    Only orders where user_id IS NULL are claimed. Orders already claimed
    or belonging to other accounts are never transferred.
    """
    if not ticket_ids:
        return []
    clean_ids = [str(t).strip().upper().replace(" ", "").replace("#", "").replace("-", "") for t in ticket_ids if t]
    clean_ids = [t for t in clean_ids if re.match(r"^GC[A-Z0-9]{4,12}$", t)][:50]
    if not clean_ids:
        return []

    with _lock:
        conn = _connect()
        try:
            placeholders = ",".join("?" for _ in clean_ids)
            query = f"SELECT public_id FROM orders WHERE public_id IN ({placeholders}) AND user_id IS NULL"
            rows = conn.execute(query, clean_ids).fetchall()
            claimed = [r["public_id"] for r in rows]
            if claimed:
                claim_placeholders = ",".join("?" for _ in claimed)
                update_query = (
                    f"UPDATE orders SET user_id = ? WHERE public_id IN ({claim_placeholders}) AND user_id IS NULL"
                )
                conn.execute(update_query, [user_id, *claimed])
                conn.commit()
            return claimed
        finally:
            conn.close()


def ping():
    """Verify database connection health and return engine type."""
    conn = _connect()
    try:
        cur = conn.execute("SELECT 1 as ping")
        row = cur.fetchone()
        is_postgres = bool(DATABASE_URL and DATABASE_URL.startswith("postgres"))
        return {
            "status": "healthy" if row else "error",
            "engine": "postgresql" if is_postgres else "sqlite",
        }
    finally:
        conn.close()



