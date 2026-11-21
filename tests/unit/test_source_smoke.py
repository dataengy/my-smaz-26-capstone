from __future__ import annotations

from urllib.parse import urlparse
import urllib.request

from tests.smoke.test_source_availability import TIMEOUT_SECONDS, _bounded_get


def test_bounded_source_probe_uses_get_timeout_and_read_limit(monkeypatch):
    captured: dict[str, object] = {}

    class Response:
        status = 206

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            captured["closed"] = True

        def read(self, limit: int) -> bytes:
            captured["read_limit"] = limit
            return b"PK\x03\x04"

    def fake_urlopen(request, *, timeout):
        captured["method"] = request.get_method()
        captured["host"] = urlparse(request.full_url).hostname
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    status, body = _bounded_get(
        "https://www.cftc.gov/example.zip",
        headers={"Range": "bytes=0-3"},
        max_bytes=4,
    )

    assert status == 206
    assert body == b"PK\x03\x04"
    assert captured == {
        "method": "GET",
        "host": "www.cftc.gov",
        "timeout": TIMEOUT_SECONDS,
        "read_limit": 4,
        "closed": True,
    }
