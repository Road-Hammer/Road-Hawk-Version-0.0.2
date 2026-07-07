from __future__ import annotations

import secrets
import sqlite3

from .database import connect

CHAIN_ROLES = frozenset({"driver", "broker", "dispatcher", "spouse", "accountant", "admin"})
CHAIN_STATUSES = frozenset({"active", "pending", "revoked"})


def _get_setting(key: str) -> str | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT value FROM chain_settings WHERE key = ?",
            (key,),
        ).fetchone()
    return row["value"] if row else None


def _set_setting(key: str, value: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO chain_settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )


def ensure_chain_profile() -> dict:
    user_key = _get_setting("local_user_key")
    if not user_key:
        user_key = f"RH-{secrets.token_hex(4).upper()}"
        _set_setting("local_user_key", user_key)

    display_name = _get_setting("local_display_name") or "Road Hawk Operator"
    if _get_setting("local_display_name") is None:
        _set_setting("local_display_name", display_name)

    return {
        "user_key": user_key,
        "display_name": display_name,
    }


def get_chain_profile() -> dict:
    return ensure_chain_profile()


def update_chain_profile(*, display_name: str) -> dict:
    cleaned = display_name.strip()
    if not cleaned:
        raise ValueError("display_name is required")
    ensure_chain_profile()
    _set_setting("local_display_name", cleaned)
    return get_chain_profile()


def list_chained_users() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, user_key, display_name, role, api_url, contact, status, notes,
                   created_at, updated_at
            FROM chained_users
            ORDER BY display_name, user_key
            """
        ).fetchall()
    return [dict(row) for row in rows]


def add_chained_user(
    *,
    user_key: str,
    display_name: str,
    role: str = "driver",
    api_url: str | None = None,
    contact: str | None = None,
    status: str = "active",
    notes: str | None = None,
) -> dict:
    cleaned_key = user_key.strip().upper()
    cleaned_name = display_name.strip()
    cleaned_role = role.strip().lower()
    cleaned_status = status.strip().lower()

    if not cleaned_key:
        raise ValueError("user_key is required")
    if not cleaned_name:
        raise ValueError("display_name is required")
    if cleaned_role not in CHAIN_ROLES:
        raise ValueError(f"Invalid role: {role}")
    if cleaned_status not in CHAIN_STATUSES:
        raise ValueError(f"Invalid status: {status}")

    local_key = ensure_chain_profile()["user_key"]
    if cleaned_key == local_key:
        raise ValueError("Cannot chain to your own user key")

    cleaned_api_url = api_url.strip() if api_url else None
    cleaned_contact = contact.strip() if contact else None
    cleaned_notes = notes.strip() if notes else None

    with connect() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO chained_users (
                    user_key, display_name, role, api_url, contact, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cleaned_key,
                    cleaned_name,
                    cleaned_role,
                    cleaned_api_url,
                    cleaned_contact,
                    cleaned_status,
                    cleaned_notes,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"User key already chained: {cleaned_key}") from exc
        chained_id = cursor.lastrowid
        row = conn.execute(
            """
            SELECT id, user_key, display_name, role, api_url, contact, status, notes,
                   created_at, updated_at
            FROM chained_users
            WHERE id = ?
            """,
            (chained_id,),
        ).fetchone()

    return dict(row)


def update_chained_user(
    chained_id: int,
    *,
    display_name: str | None = None,
    role: str | None = None,
    api_url: str | None = None,
    contact: str | None = None,
    status: str | None = None,
    notes: str | None = None,
) -> dict:
    updates: list[str] = []
    values: list[object] = []

    if display_name is not None:
        cleaned_name = display_name.strip()
        if not cleaned_name:
            raise ValueError("display_name cannot be empty")
        updates.append("display_name = ?")
        values.append(cleaned_name)

    if role is not None:
        cleaned_role = role.strip().lower()
        if cleaned_role not in CHAIN_ROLES:
            raise ValueError(f"Invalid role: {role}")
        updates.append("role = ?")
        values.append(cleaned_role)

    if api_url is not None:
        updates.append("api_url = ?")
        values.append(api_url.strip() or None)

    if contact is not None:
        updates.append("contact = ?")
        values.append(contact.strip() or None)

    if status is not None:
        cleaned_status = status.strip().lower()
        if cleaned_status not in CHAIN_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        updates.append("status = ?")
        values.append(cleaned_status)

    if notes is not None:
        updates.append("notes = ?")
        values.append(notes.strip() or None)

    if not updates:
        raise ValueError("No fields to update")

    updates.append("updated_at = datetime('now')")
    values.append(chained_id)

    with connect() as conn:
        result = conn.execute(
            f"UPDATE chained_users SET {', '.join(updates)} WHERE id = ?",
            values,
        )
        if result.rowcount == 0:
            raise ValueError(f"Chained user not found: {chained_id}")

        row = conn.execute(
            """
            SELECT id, user_key, display_name, role, api_url, contact, status, notes,
                   created_at, updated_at
            FROM chained_users
            WHERE id = ?
            """,
            (chained_id,),
        ).fetchone()

    return dict(row)


def remove_chained_user(chained_id: int) -> None:
    with connect() as conn:
        result = conn.execute("DELETE FROM chained_users WHERE id = ?", (chained_id,))
        if result.rowcount == 0:
            raise ValueError(f"Chained user not found: {chained_id}")