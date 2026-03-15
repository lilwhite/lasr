import json
from typing import Dict, Tuple
from urllib.request import Request, urlopen


USER_AGENT = "LASR-PressFetcher/2.0 (+https://lasr-info.es)"


def fetch_bytes(url: str, timeout: int) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as response:
        return response.read()


def fetch_json(url: str, timeout: int) -> Tuple[Dict[str, str], object]:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as response:
        headers = {
            "x-wp-total": response.headers.get("X-WP-Total", ""),
            "x-wp-totalpages": response.headers.get("X-WP-TotalPages", ""),
        }
        payload = json.loads(response.read().decode("utf-8"))
        return headers, payload
