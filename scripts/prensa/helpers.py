import hashlib
import json
import re
import unicodedata
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


TRACKING_QUERY_PREFIXES = (
    "utm_",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def normalize_text(value: str) -> str:
    value = value or ""
    value = unescape(value)
    value = value.lower().strip()
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = re.sub(r"\s+", " ", value)
    return value


def strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def canonicalize_url(url: str) -> str:
    if not url:
        return ""

    parsed = urlparse(url.strip())
    netloc = parsed.netloc.lower()
    if netloc.endswith(":80"):
        netloc = netloc[:-3]
    if netloc.endswith(":443"):
        netloc = netloc[:-4]

    path = parsed.path or ""
    if path != "/":
        path = path.rstrip("/")

    query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not any(k.lower().startswith(prefix) for prefix in TRACKING_QUERY_PREFIXES)
    ]
    cleaned = parsed._replace(
        fragment="", query=urlencode(query), netloc=netloc, path=path
    )
    return urlunparse(cleaned)


def parse_date(raw_date: str) -> str:
    if not raw_date:
        return ""

    raw_date = raw_date.strip()
    if not raw_date:
        return ""

    for parser in (
        _parse_rfc822,
        _parse_iso,
    ):
        parsed = parser(raw_date)
        if parsed:
            return parsed

    return ""


def _parse_rfc822(raw_date: str) -> str:
    try:
        dt = parsedate_to_datetime(raw_date)
        return dt.date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return ""


def _parse_iso(raw_date: str) -> str:
    candidate = raw_date.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(candidate)
        return dt.date().isoformat()
    except ValueError:
        return ""


def stable_id(url: str, title: str) -> str:
    base = url or normalize_text(title)
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]
    return f"news-{digest}"


def normalize_title_key(title: str) -> str:
    text = normalize_text(title)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
