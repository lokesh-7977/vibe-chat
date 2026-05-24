from __future__ import annotations

import re
from urllib.parse import urlparse, parse_qs, urlunparse


_YOUTUBE_ID_RE = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)")


def normalize_website_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    try:
        parsed = urlparse(u)
        # drop fragments, normalize scheme/host
        scheme = (parsed.scheme or "").lower()
        netloc = (parsed.netloc or "").lower()
        path = parsed.path or ""
        # strip trailing slash except root
        if path.endswith("/") and path != "/":
            path = path[:-1]
        normalized = parsed._replace(scheme=scheme, netloc=netloc, fragment="", path=path)
        return urlunparse(normalized)
    except Exception:
        return u


def youtube_cache_key(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    m = _YOUTUBE_ID_RE.search(u)
    if m:
        return f"youtube:{m.group(1)}"
    try:
        parsed = urlparse(u)
        if "youtube.com" in (parsed.netloc or "").lower():
            qs = parse_qs(parsed.query or "")
            vid = (qs.get("v") or [""])[0]
            if vid:
                return f"youtube:{vid}"
    except Exception:
        pass
    return f"youtube_url:{normalize_website_url(u)}"

