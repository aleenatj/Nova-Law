"""Derive session device fields from User-Agent and client ``device`` context."""

from __future__ import annotations

from typing import Any, TypedDict

from user_agents import parse as parse_user_agent  # type: ignore[import-untyped]


class SessionDeviceFields(TypedDict, total=False):
    device_type: str | None
    browser: str | None
    client_os: str | None
    country: str | None
    locale: str | None
    timezone: str | None
    is_bot: bool


def _country_hint_from_locale(locale: str | None) -> str | None:
    """Best-effort region from BCP-47 tag (e.g. ``en-US`` → ``US``); may be wrong for some tags."""
    if not locale:
        return None
    parts = locale.replace("_", "-").split("-")
    for part in reversed(parts):
        p = part.strip().upper()
        if len(p) == 2 and p.isalpha():
            return p
    return None


def _trim(s: str | None, max_len: int = 512) -> str | None:
    if s is None:
        return None
    t = str(s).strip()
    if not t:
        return None
    return t[:max_len]


def _browser_string(ua: Any) -> str | None:
    fam = getattr(ua.browser, "family", None) or ""
    ver = getattr(ua.browser, "version_string", None) or ""
    parts = " ".join(p for p in (fam.strip(), ver.strip()) if p)
    return parts or None


def _os_string(ua: Any) -> str | None:
    fam = getattr(ua.os, "family", None) or ""
    ver = getattr(ua.os, "version_string", None) or ""
    parts = " ".join(p for p in (fam.strip(), ver.strip()) if p)
    return parts or None


def _device_type_from_ua(ua: Any) -> str | None:
    if getattr(ua, "is_bot", False):
        return None
    if ua.is_tablet:
        return "tablet"
    if ua.is_mobile:
        return "mobile"
    if ua.is_pc:
        return "desktop"
    return "desktop"


def parse_session_device_fields(
    user_agent: str | None,
    device: dict[str, Any] | None,
) -> SessionDeviceFields:
    """
    Combine UA parsing (device_type, browser, OS) with client ``device`` payload
    (country, locale, timezone). Country is not available from UA alone; it may
    be supplied by the client (e.g. CDN geo header surfaced to the browser).
    """
    dev = device if isinstance(device, dict) else {}
    country = _trim(dev.get("country"), max_len=8)
    locale = _trim(dev.get("locale"), max_len=64)
    tz_name = _trim(dev.get("timezone"), max_len=128)
    if not country and locale:
        country = _country_hint_from_locale(locale)

    ua_raw = _trim(user_agent, max_len=2048)
    device_type: str | None = None
    browser: str | None = None
    client_os: str | None = None
    is_bot = False

    if ua_raw:
        try:
            parsed = parse_user_agent(ua_raw)
            is_bot = bool(getattr(parsed, "is_bot", False))
            device_type = _device_type_from_ua(parsed)
            browser = _browser_string(parsed)
            client_os = _os_string(parsed)
        except Exception:
            pass

    return SessionDeviceFields(
        device_type=device_type,
        browser=browser,
        client_os=client_os,
        country=country,
        locale=locale,
        timezone=tz_name,
        is_bot=is_bot,
    )


def apply_parsed_device_to_session(sess: Any, parsed: SessionDeviceFields) -> None:
    """Backfill null session columns from a later event (same session id)."""
    if parsed.get("device_type") and getattr(sess, "device_type", None) in (None, ""):
        sess.device_type = parsed["device_type"]
    if parsed.get("browser") and getattr(sess, "browser", None) in (None, ""):
        sess.browser = parsed["browser"]
    if parsed.get("client_os") and getattr(sess, "client_os", None) in (None, ""):
        sess.client_os = parsed["client_os"]
    if parsed.get("country") and getattr(sess, "country", None) in (None, ""):
        sess.country = parsed["country"]
    if parsed.get("locale") and getattr(sess, "locale", None) in (None, ""):
        sess.locale = parsed["locale"]
    if parsed.get("timezone") and getattr(sess, "client_timezone", None) in (None, ""):
        sess.client_timezone = parsed["timezone"]
    if parsed.get("is_bot"):
        sess.is_bot = True
