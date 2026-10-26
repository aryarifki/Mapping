"""Shared HTTP helpers for the IDX/KSEI endpoint mapping collectors.

Stdlib only (no third-party deps) so the scripts run anywhere.

Two header profiles matter, and they are NOT interchangeable:

* KSEI  -- a plain nginx/Varnish front end. Any sane User-Agent works. Endpoints
           under /api/ additionally reject requests that do not ask for JSON with
           HTTP 405 {"message": "Backend accept only json communication."}.
* IDX   -- behind Cloudflare. Requests that omit the Sec-Fetch-* headers get a
           "Just a moment..." 403 challenge. Sending a realistic browser header
           set (including Sec-Fetch-Dest/Mode/Site) passes without any JS
           execution. IDX also rate-limits, so pace requests.
"""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

# This sandbox has no working IPv6 resolver: an AF_UNSPEC getaddrinfo() (what
# urllib uses by default) fails outright with EAI_AGAIN, while AF_INET succeeds.
# Force IPv4 so the collectors work here and everywhere else.
_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if family in (0, socket.AF_UNSPEC):
        family = socket.AF_INET
    return _orig_getaddrinfo(host, port, family, type, proto, flags)


socket.getaddrinfo = _ipv4_getaddrinfo

UA_DESKTOP = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

KSEI_HEADERS = {
    "User-Agent": UA_DESKTOP,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
}

IDX_HEADERS = {
    "User-Agent": UA_DESKTOP,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
    # Without these three, Cloudflare serves the JS challenge instead of JSON.
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Referer": "https://www.idx.co.id/id/market-data",
}


class Result:
    def __init__(self, url, status, body, content_type, elapsed, error=None):
        self.url = url
        self.status = status
        self.body = body  # bytes
        self.content_type = content_type
        self.elapsed = elapsed
        self.error = error

    @property
    def is_json(self) -> bool:
        head = self.body[:1].lstrip() or self.body.lstrip()[:1]
        return head in (b"{", b"[")

    @property
    def is_challenge(self) -> bool:
        return b"Just a moment" in self.body[:4000] or b"cf-browser-verification" in self.body[:4000]

    def json(self):
        return json.loads(self.body.decode("utf-8", "replace"))

    def __repr__(self):
        return f"<Result {self.status} {len(self.body)}B {self.url}>"


def get(url, headers, params=None, timeout=30, retries=3, backoff=8.0, pace=0.0, method="GET", body=None):
    """GET/POST a URL, retrying on Cloudflare challenges / 5xx / transport errors.

    `pace` is a polite delay applied before every attempt (rate-limit friendly).
    """
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params, doseq=True)

    data = None
    if body is not None:
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        headers = dict(headers)
        headers.setdefault("Content-Type", "application/json")

    last = None
    for attempt in range(1, retries + 1):
        if pace:
            time.sleep(pace)
        started = time.time()
        req = urllib.request.Request(url, headers=headers, data=data, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                res = Result(url, resp.status, body, resp.headers.get("Content-Type", ""), time.time() - started)
        except urllib.error.HTTPError as exc:
            body = exc.read()
            res = Result(url, exc.code, body, exc.headers.get("Content-Type", "") if exc.headers else "", time.time() - started)
        except Exception as exc:  # transport / DNS / timeout
            res = Result(url, 0, b"", "", time.time() - started, error=str(exc))

        last = res
        # Retry only on things that are plausibly transient. Status 0 covers the
        # sandbox's intermittent EAI_AGAIN DNS failures, which clear on a retry.
        transient = res.status in (0, 429, 500, 502, 503, 504) or res.is_challenge
        if not transient or attempt == retries:
            return res
        wait = backoff * attempt
        print(f"      ... {res.status}{' (CF challenge)' if res.is_challenge else ''}, retry {attempt}/{retries - 1} in {wait:.0f}s")
        time.sleep(wait)
    return last


def save(result: Result, path, meta=None):
    """Persist the raw body verbatim, plus a small .meta.json sidecar."""
    import os

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(result.body)
    if meta is not None:
        with open(path + ".meta.json", "w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2, ensure_ascii=False)
    return len(result.body)


def status_label(result: Result) -> str:
    # A 200 is "active" as long as the body is not an HTML error page. Some IDX
    # and AKSes routes legitimately answer with a bare scalar (e.g. "2026-10-26")
    # rather than an object, so we cannot insist on parseable JSON here.
    body = result.body.lstrip()[:1]
    if result.status == 200 and body and body != b"<":
        return "active"
    if result.status == 422:
        return "needs-params"
    if result.status in (401, 403) and not result.is_challenge:
        return "forbidden"
    if result.is_challenge:
        return "waf-challenge"
    if result.status in (301, 302, 404):
        return "dead"
    if result.status == 0:
        return "unreachable"
    return f"http-{result.status}"


def write_json(path, payload):
    import os

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
