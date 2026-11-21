#!/usr/bin/env python3
"""Run bounded DNS/HTTPS and source-shaped connectivity probes.

This is a reachability check, not a data acquisition job. It reads at most 8 KiB
from each response and never writes response bodies to disk. If the current
sandbox blocks DNS sockets, rerun this script only through an approved network
diagnostic path; it does not attempt to bypass the sandbox.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode, urlsplit

TIMEOUT_SECONDS = 12
MAX_RESPONSE_BYTES = 8192
USER_AGENT = "my-smaz-26-capstone-connectivity-check/1.0"
CFTC_GOLD_API = "https://publicreporting.cftc.gov/resource/72hh-3qpy.json?" + urlencode(
    {
        "$limit": "1",
        "$select": "report_date_as_yyyy_mm_dd,contract_market_name",
        "$where": "contract_market_name like '%GOLD%'",
        "$order": "report_date_as_yyyy_mm_dd DESC",
    }
)
_today = datetime.now(timezone.utc).date()
_sample_start = (_today - timedelta(days=10)).strftime("%Y%m%d")
_sample_end = _today.strftime("%Y%m%d")
STOOQ_GLD_SAMPLE = "https://stooq.com/q/d/l/?" + urlencode(
    {"s": "gld.us", "i": "d", "d1": _sample_start, "d2": _sample_end}
)

PROBES: tuple[tuple[str, str], ...] = (
    ("github", "https://github.com/"),
    ("pypi", "https://pypi.org/simple/"),
    ("cftc_reports", "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"),
    (
        "cftc_disaggregated_futures_only_gold_api",
        CFTC_GOLD_API,
    ),
    (
        "yahoo_gld_5d_chart",
        "https://query1.finance.yahoo.com/v8/finance/chart/GLD?range=5d&interval=1d",
    ),
    ("fred", "https://fred.stlouisfed.org/"),
    ("stooq_gld_daily_sample", STOOQ_GLD_SAMPLE),
    ("alpha_vantage", "https://www.alphavantage.co/"),
)


def resolve(host: str) -> list[str]:
    results = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    return sorted({result[4][0] for result in results})


def curl_fallback(url: str, timeout: int) -> dict[str, Any]:
    """Check the FRED landing page with curl without retaining its response body."""
    command = [
        "curl",
        "--silent",
        "--show-error",
        "--location",
        "--output",
        "/dev/null",
        "--write-out",
        "%{http_code}\t%{remote_ip}",
        "--connect-timeout",
        str(timeout),
        "--max-time",
        str(timeout),
        url,
    ]
    try:
        response = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}

    fields = response.stdout.strip().split("\t", maxsplit=1)
    result: dict[str, Any] = {"exit_code": response.returncode}
    if fields and fields[0].isdigit():
        result["http_status"] = int(fields[0])
    if len(fields) == 2 and fields[1]:
        result["remote_ip"] = fields[1]
    if response.stderr.strip():
        result["error"] = response.stderr.strip()[:500]
    result["reachable"] = (
        response.returncode == 0 and 100 <= result.get("http_status", 0) < 600
    )
    return result


def probe(name: str, url: str, timeout: int) -> dict[str, Any]:
    host = urlsplit(url).hostname
    if host is None:
        raise ValueError(f"probe URL has no hostname: {url}")
    result: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "name": name,
        "host": host,
        "url": url,
    }
    try:
        result["dns_addresses"] = resolve(host)
    except OSError as exc:
        result.update(dns_error=f"{type(exc).__name__}: {exc}", outcome="dns_error")
        return result

    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/csv,text/html,*/*"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result.update(
                http_status=response.status,
                content_type=response.headers.get("Content-Type"),
                outcome="http_response",
            )
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                result["retry_after"] = retry_after
            try:
                body = response.read(MAX_RESPONSE_BYTES)
                result["bytes_read"] = len(body)
                if name == "cftc_disaggregated_futures_only_gold_api":
                    payload = json.loads(body)
                    rows = payload if isinstance(payload, list) else []
                    result["records_sampled"] = len(rows)
                    result["content_valid"] = bool(rows) and all(
                        isinstance(row, dict) and row.get("contract_market_name") == "GOLD"
                        for row in rows
                    )
                    if rows:
                        if isinstance(rows[0], dict):
                            result["latest_report_date"] = rows[0].get("report_date_as_yyyy_mm_dd")
                elif name == "yahoo_gld_5d_chart":
                    payload = json.loads(body)
                    chart = payload.get("chart", {}) if isinstance(payload, dict) else {}
                    chart = chart if isinstance(chart, dict) else {}
                    candidates = chart.get("result") or []
                    first = candidates[0] if isinstance(candidates, list) and candidates else {}
                    first = first if isinstance(first, dict) else {}
                    meta = first.get("meta", {})
                    meta = meta if isinstance(meta, dict) else {}
                    timestamps = first.get("timestamp") or []
                    result["symbol"] = meta.get("symbol")
                    result["bars_sampled"] = len(timestamps) if isinstance(timestamps, list) else 0
                    result["content_valid"] = (
                        result["symbol"] == "GLD" and result["bars_sampled"] > 0
                    )
                elif name == "stooq_gld_daily_sample":
                    lines = body.decode("utf-8", errors="replace").splitlines()
                    parsed = list(csv.reader(io.StringIO("\n".join(lines))))
                    result["header"] = parsed[0] if parsed else []
                    header_valid = result["header"] == [
                        "Date",
                        "Open",
                        "High",
                        "Low",
                        "Close",
                        "Volume",
                    ]
                    result["records_sampled"] = max(len(parsed) - 1, 0) if header_valid else 0
                    result["content_valid"] = (
                        header_valid and result["records_sampled"] > 0
                    )
                if result.get("content_valid") is False:
                    result["outcome"] = "content_mismatch"
            except (TimeoutError, OSError) as exc:
                result["body_read_error"] = f"{type(exc).__name__}: {exc}"
                result["outcome"] = "body_read_error"
    except urllib.error.HTTPError as exc:
        result.update(
            http_status=exc.code,
            outcome="http_error",
            retry_after=exc.headers.get("Retry-After"),
        )
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result.update(https_error=f"{type(exc).__name__}: {exc}", outcome="https_error")
        if name == "fred":
            result["curl_fallback"] = curl_fallback(url, timeout)
            if result["curl_fallback"].get("reachable"):
                # Preserve urllib's failure while distinguishing it from host unreachability.
                result["outcome"] = "client_specific_error"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        action="append",
        choices=[name for name, _ in PROBES],
        help="run only this named probe (repeat the option to select several)",
    )
    parser.add_argument("--timeout", type=int, default=TIMEOUT_SECONDS, help="per-request timeout in seconds")
    args = parser.parse_args(argv)
    if args.timeout < 1:
        parser.error("--timeout must be at least 1 second")

    failed_probe = False
    for name, url in PROBES:
        if args.only and name not in args.only:
            continue
        result = probe(name, url, args.timeout)
        print(json.dumps(result, sort_keys=True))
        failed_probe |= result["outcome"] in {
            "dns_error",
            "https_error",
            "body_read_error",
            "content_mismatch",
        }
    # HTTP 4xx/5xx is evidence of a reachable server and is reported separately.
    # In particular, don't retry a 429 here: honor the provider's rate limit.
    return 1 if failed_probe else 0


if __name__ == "__main__":
    sys.exit(main())
