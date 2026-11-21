"""Opt-in, bounded reachability checks for configured market and CFTC sources.

Run with ``make test-source-smoke``. The tests read at most a small response
prefix and never write or refresh local snapshots.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
import os
from pathlib import Path
import sys
from urllib.parse import quote
import urllib.error
import urllib.request

import pandas as pd
import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("CAPSTONE_SOURCE_SMOKE") != "1",
    reason="live provider checks are opt-in; run make test-source-smoke",
)

TIMEOUT_SECONDS = 8
YAHOO_MAX_BYTES = 65_536
CFTC_PREFIX_BYTES = 4


def _bounded_get(
    url: str,
    *,
    headers: dict[str, str],
    max_bytes: int,
) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        body = response.read(max_bytes)
        return response.status, body


def _project_config():
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "src"))
    from capstone.config import read_config
    from capstone.data import CFTC_URL, CFTC_USER_AGENT

    config = read_config(root / "config/config.yml", root / "config/settings.yml")
    return root, config, CFTC_URL, CFTC_USER_AGENT


def test_configured_market_provider_endpoints_are_reachable():
    """Check every active configured ticker through its provider's small endpoint."""
    _, config, _, _ = _project_config()
    from capstone.data import BINANCE_KLINES_URL, _active_symbols, _market_source

    symbols, required = _active_symbols(config)
    errors: list[str] = []

    for name, default_ticker in symbols.items():
        provider, ticker, _ = _market_source(name, default_ticker, config)
        if provider == "binance":
            url = f"{BINANCE_KLINES_URL}?symbol={quote(ticker)}&interval=1d&limit=1"
        else:
            url = (
                "https://query1.finance.yahoo.com/v8/finance/chart/"
                f"{quote(ticker, safe='')}?range=5d&interval=1d"
            )
        try:
            status, body = _bounded_get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; capstone-source-smoke/1.0)"},
                max_bytes=YAHOO_MAX_BYTES,
            )
            if status != 200:
                errors.append(f"{provider} {name} ({ticker}): HTTP {status}")
                continue
            payload = json.loads(body)
            if provider == "binance":
                if not isinstance(payload, list) or not payload:
                    errors.append(f"Binance Spot {name} ({ticker}): no recent klines")
                    continue
                print(f"AVAILABLE Binance Spot source {name} ({ticker}), HTTP {status}")
            else:
                result = (payload.get("chart") or {}).get("result") or []
                if not result or not result[0].get("timestamp"):
                    errors.append(f"Yahoo Finance {name} ({ticker}): no recent chart observations")
                    continue
                role = "required" if name in required else "optional"
                print(f"AVAILABLE Yahoo Finance {role} source {name} ({ticker}), HTTP {status}")
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{provider} {name} ({ticker}): {type(exc).__name__}: {exc}")

    assert not errors, "Configured market-source smoke failures:\n- " + "\n- ".join(errors)


def test_cftc_archives_and_release_evidence_are_reachable_and_zip_shaped():
    """Check configured historical archives and manifest evidence pages, bounded."""
    root, config, cftc_url, user_agent = _project_config()
    first_year = date.fromisoformat(str(config.get("start", "2018-01-01"))[:10]).year
    end = config.get("end")
    last_year = (
        (date.fromisoformat(str(end)[:10]) - timedelta(days=1)).year
        if end else date.today().year
    )
    errors: list[str] = []
    headers = {
        "User-Agent": user_agent,
        "Range": f"bytes=0-{CFTC_PREFIX_BYTES - 1}",
        "Accept-Encoding": "identity",
    }

    for year in range(first_year, last_year + 1):
        url = cftc_url.format(year=year)
        try:
            status, prefix = _bounded_get(url, headers=headers, max_bytes=CFTC_PREFIX_BYTES)
            if status not in (200, 206):
                errors.append(f"CFTC COT archive {year}: HTTP {status} ({url})")
            elif not prefix.startswith(b"PK\x03\x04"):
                errors.append(f"CFTC COT archive {year}: response is not ZIP-shaped (HTTP {status})")
            else:
                print(f"AVAILABLE CFTC COT archive {year}, HTTP {status}, read {len(prefix)} bytes")
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            errors.append(f"CFTC COT archive {year}: {type(exc).__name__}: {exc} ({url})")

    manifest = pd.read_csv(root / config["release_manifest"], dtype=str)
    for url in sorted(set(manifest["source_url"].dropna())):
        try:
            status, body = _bounded_get(url, headers={"User-Agent": user_agent}, max_bytes=512)
            if status != 200 or not body:
                errors.append(f"COT release-evidence page: HTTP {status}, empty={not body} ({url})")
            else:
                print(f"AVAILABLE COT release-evidence page, HTTP {status}: {url}")
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            errors.append(f"COT release-evidence page: {type(exc).__name__}: {exc} ({url})")

    assert not errors, "CFTC source smoke failures:\n- " + "\n- ".join(errors)
