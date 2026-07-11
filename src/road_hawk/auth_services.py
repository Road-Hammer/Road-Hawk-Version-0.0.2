from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from .config import is_externally_exposed
from .database import connect

APP_ROLES = frozenset({"driver", "broker", "dispatcher", "spouse", "accountant", "admin"})
SESSION_HOURS = 12
_TRUE_VALUES = {"1", "true", "yes", "on"}


def auth_required() -> bool:
    """Require auth when explicitly enabled or whenever the API crosses loopback."""
    explicit = os.environ.get("ROAD_HAWK_AUTH_REQUIRED", "").strip().lower()
    return explicit in _TRUE_VALUES or is_externally_exposed()


def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return digest.hex()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_ts(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def ensure_bootstrap_admin() -> None:
    admin_user = os.environ.get("ROAD_HAWK_ADMIN_USER", "").strip()
    admin_password = os.environ.get("ROAD_HAWK_ADMIN_PASSWORD", "").strip()
    if not admin_user or not admin_password:
        return

    with connect() as conn:
        count = conn.execute("SELECT COUNT(*) AS count FROM app_users").fetchone()["count"]
        if count:
            return

    create_user(
        username=admin_user,
        password=admin_password,
        role="admin",
        display_name=admin_user,
        allow_initial_admin=True,
    )


def create_user(
    *,
    username: str,
    password: str,
    role: str = "driver",
    display_name: str | None = None,
    allow_initial_admin: bool = False,
) -> dict:
    cleaned_username = username.strip().lower()
    cleaned_role = role.strip().lower()
    cleaned_display_name = (display_name or username).strip()

    if not cleaned_username:
        raise ValueError("username is required")
    if not password:
        raise ValueError("password is required")
    if cleaned_role not in APP_ROLES:
        raise ValueError(f"Invalid role: {role}")

    with connect() as conn:
        user_count = conn.execute("SELECT COUNT(*) AS count FROM app_users").fetchone()["count"]

    if auth_required() and user_count == 0 and not allow_initial_admin:
        raise ValueError(
            "Remote first-user bootstrap is disabled. Configure ROAD_HAWK_ADMIN_USER "
            "and ROAD_HAWK_ADMIN_PASSWORD on the server, then restart Road Hawk."
        )

    salt = secrets.token_hex(16)
    password_hash = _hash_password(password, salt)

    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO app_users (username, password_hash, password_salt, role, display_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                cleaned_username,
                password_hash,
                salt,
                cleaned_role,
                cleaned_display_name,
            ),
        )
        user_id = cursor.lastrowid
        row = conn.execute(
            """
            SELECT id, username, role, display_name, active, created_at, last_login_at
            FROM app_users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    return dict(row)


def authenticate_user(username: str, password: str) -> dict:
    cleaned_username = username.strip().lower()
    if not cleaned_username or not password:
        raise ValueError("username and password are required")

    with connect() as conn:
        row = conn.execute(
            """
            SELECT id, username, password_hash, password_salt, role, display_name, active
            FROM app_users
            WHERE username = ?
            """,
            (cleaned_username,),
        ).fetchone()

    if not row or not row["active"]:
        raise ValueError("Invalid username or password")

    expected = _hash_password(password, row["password_salt"])
    if not secrets.compare_digest(expected, row["password_hash"]):
        raise ValueError("Invalid username or password")

    return {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"],
        "display_name": row["display_name"],
    }


def create_session(user_id: int) -> dict:
    token = secrets.token_urlsafe(32)
    expires_at = _utc_now() + timedelta(hours=SESSION_HOURS)

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO app_sessions (token, user_id, expires_at)
            VALUES (?, ?, ?)
            """,
            (token, user_id, _format_ts(expires_at)),
        )
        conn.execute(
            "UPDATE app_users SET last_login_at = datetime('now') WHERE id = ?",
            (user_id,),
        )

    return {
        "token": token,
        "expires_at": _format_ts(expires_at),
    }


def get_user_from_token(token: str | None) -> dict | None:
    if not token:
        return None

    with connect() as conn:
        row = conn.execute(
            """
            SELECT
                u.id,
                u.username,
                u.role,
                u.display_name,
                u.active,
                s.expires_at
            FROM app_sessions s
            JOIN app_users u ON u.id = s.user_id
            WHERE s.token = ?
            """,
            (token.strip(),),
        ).fetchone()

    if not row or not row["active"]:
        return None

    expires_at = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    if _utc_now() > expires_at:
        revoke_session(token)
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"],
        "display_name": row["display_name"],
    }


def revoke_session(token: str | None) -> None:
    if not token:
        return
    with connect() as conn:
        conn.execute("DELETE FROM app_sessions WHERE token = ?", (token.strip(),))


def auth_status(token: str | None = None) -> dict:
    user = get_user_from_token(token)
    return {
        "auth_required": auth_required(),
        "authenticated": user is not None,
        "user": user,
        "roles": sorted(APP_ROLES),
    }
