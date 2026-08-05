"""Run repeatable authenticated stakeholder read-load validation."""

from __future__ import annotations

import os
import ssl
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from http.cookiejar import CookieJar
from urllib.parse import urlencode
from urllib.request import (
    BaseHandler,
    HTTPCookieProcessor,
    HTTPSHandler,
    Request,
    build_opener,
    urlopen,
)


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round(percentile * len(ordered)) - 1))
    return ordered[index]


def main() -> None:
    base_url = os.getenv("LOAD_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
    username = os.environ["E2E_USERNAME"]
    password = os.environ["E2E_PASSWORD"]
    sequential_count = int(os.getenv("LOAD_SEQUENTIAL_COUNT", "200"))
    concurrent_count = int(os.getenv("LOAD_CONCURRENT_COUNT", "100"))
    workers = int(os.getenv("LOAD_WORKERS", "10"))
    ca_file = os.getenv("LOAD_CA_FILE")
    tls_context = ssl.create_default_context(cafile=ca_file) if ca_file else None

    cookie_jar = CookieJar()
    handlers: list[BaseHandler] = [HTTPCookieProcessor(cookie_jar)]
    if tls_context:
        handlers.append(HTTPSHandler(context=tls_context))
    opener = build_opener(*handlers)
    login_url = f"{base_url}/accounts/login/"
    with opener.open(login_url, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"Login page returned HTTP {response.status}.")
    csrf_token = next(
        cookie.value for cookie in cookie_jar if cookie.name == "csrftoken"
    )
    login_data = urlencode(
        {
            "csrfmiddlewaretoken": csrf_token,
            "username": username,
            "password": password,
            "next": "/stakeholders/directory/",
        }
    ).encode()
    request = Request(
        login_url,
        data=login_data,
        headers={"Referer": login_url},
        method="POST",
    )
    with opener.open(request, timeout=30) as response:
        if response.status != 200 or "/stakeholders/directory/" not in response.url:
            raise RuntimeError(
                "Authenticated login did not reach the stakeholder directory."
            )

    cookie_header = "; ".join(f"{cookie.name}={cookie.value}" for cookie in cookie_jar)
    directory_url = f"{base_url}/stakeholders/directory/"

    def fetch_directory(_: int) -> float:
        started_at = time.perf_counter()
        request = Request(directory_url, headers={"Cookie": cookie_header})
        with urlopen(request, timeout=30, context=tls_context) as response:
            if response.status != 200:
                raise RuntimeError(f"Directory returned HTTP {response.status}.")
            response.read()
        return time.perf_counter() - started_at

    sequential = [fetch_directory(index) for index in range(sequential_count)]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        concurrent = list(executor.map(fetch_directory, range(concurrent_count)))

    all_timings = sequential + concurrent
    print(
        "Authenticated load probe passed: "
        f"{sequential_count} sequential + {concurrent_count} concurrent reads, "
        f"workers={workers}, mean={statistics.mean(all_timings):.3f}s, "
        f"p95={_percentile(all_timings, 0.95):.3f}s, "
        f"max={max(all_timings):.3f}s."
    )


if __name__ == "__main__":
    main()
