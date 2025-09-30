"""Helpers for consistent API component naming and hashing."""

from __future__ import annotations

from typing import Optional

_ALLOWED_METHODS = {
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "PATCH",
    "OPTIONS",
    "HEAD",
}


def normalize_http_method(http_method: Optional[str]) -> Optional[str]:
    """Return an upper-cased HTTP method or None when it is missing/unknown."""
    if not http_method:
        return None
    method = http_method.strip().upper()
    if not method or method == "UNKNOWN":
        return None
    return method


def format_api_component_name(
    http_method: Optional[str],
    method_name: Optional[str],
    fallback_url: Optional[str] = None,
) -> Optional[str]:
    """Build the display name for an API component.

    Rules:
    - Preferred form is `GET:selectUser` (HTTP method + method name).
    - If the HTTP method is missing/unknown, fall back to just the method name.
    - If the method name is omitted but we still have a method (e.g. GET) and
      a reasonable fallback URL, return `GET:/api/users` style so the caller has
      something to render.
    - As a last resort, return the fallback URL or None when everything is
      missing.
    """
    normalized_method = normalize_http_method(http_method)
    normalized_name = method_name.strip() if method_name else ""

    if normalized_method and normalized_name:
        return f"{normalized_method}:{normalized_name}"

    if normalized_name:
        return normalized_name

    if normalized_method and fallback_url:
        safe_url = fallback_url.strip()
        return f"{normalized_method}:{safe_url}" if safe_url else normalized_method

    return fallback_url.strip() if fallback_url else None


def build_api_identity_key(url_pattern: str, http_method: Optional[str]) -> str:
    """Create a stable identity key for hashing existing API_URL entries."""
    normalized_method = normalize_http_method(http_method) or ""
    normalized_url = (url_pattern or "").strip().lower()
    return f"{normalized_method}::{normalized_url}"
