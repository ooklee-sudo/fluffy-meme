"""Polite HTTP client: rate limit, retries with backoff, and an on-disk cache."""
import hashlib
import os
import time

import requests


class Client:
    def __init__(self, user_agent, rps, cache_dir=None, session=None, max_retries=5,
                 retry_status=(429, 500, 502, 503, 504), first_delay=2.0):
        self.s = session or requests.Session()
        self.s.headers.update({"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"})
        self.min_gap = 1.0 / rps
        self._last = 0.0
        self.cache_dir = cache_dir
        self.max_retries = max_retries
        self.retry_status = tuple(retry_status)
        self.first_delay = first_delay
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

    def _wait(self):
        gap = time.monotonic() - self._last
        if gap < self.min_gap:
            time.sleep(self.min_gap - gap)
        self._last = time.monotonic()

    def _cache_path(self, url, params, headers):
        key = repr((url, sorted((params or {}).items()), sorted((headers or {}).items())))
        return os.path.join(self.cache_dir, hashlib.sha1(key.encode()).hexdigest())

    def size(self, url):
        """Content length from a HEAD request (cached)."""
        path = self._cache_path(url, {"_method": "HEAD"}, None) if self.cache_dir else None
        if path and os.path.exists(path):
            with open(path) as f:
                return int(f.read())
        delay = self.first_delay
        for attempt in range(self.max_retries):
            self._wait()
            try:
                r = self.s.head(url, timeout=60, allow_redirects=True)
            except requests.RequestException:
                time.sleep(delay); delay *= 2
                continue
            if r.status_code in self.retry_status:
                time.sleep(delay); delay *= 2
                continue
            if r.status_code != 200 or "Content-Length" not in r.headers:
                raise RuntimeError(f"HEAD {url}: HTTP {r.status_code}")
            n = int(r.headers["Content-Length"])
            if path:
                with open(path, "w") as f:
                    f.write(str(n))
            return n
        raise RuntimeError(f"Giving up after {self.max_retries} attempts: HEAD {url}")

    def get(self, url, params=None, headers=None, ok_status=(200,), cache=True):
        """Return (status, bytes). Cached only for successful responses."""
        path = self._cache_path(url, params, headers) if (self.cache_dir and cache) else None
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                return 200, f.read()
        delay = self.first_delay
        for attempt in range(self.max_retries):
            self._wait()
            try:
                r = self.s.get(url, params=params, headers=headers, timeout=60)
            except requests.RequestException:
                time.sleep(delay); delay *= 2
                continue
            if r.status_code in self.retry_status:
                time.sleep(delay); delay *= 2
                continue
            if r.status_code in ok_status and path:
                with open(path, "wb") as f:
                    f.write(r.content)
            return r.status_code, r.content
        raise RuntimeError(f"Giving up after {self.max_retries} attempts: {url} {params}")
