"""Tests: URL validation and SSRF protection (Module B, security)."""
from __future__ import annotations

import socket

import pytest

from app.services import scrape_service
from app.services.exceptions import ScrapeError


class TestSchemeAndPort:
    def test_ftp_rejected(self) -> None:
        with pytest.raises(ScrapeError):
            scrape_service.validate_public_http_url("ftp://example.com/job")

    def test_file_rejected(self) -> None:
        with pytest.raises(ScrapeError):
            scrape_service.validate_public_http_url("file:///etc/passwd")

    def test_no_scheme_rejected(self) -> None:
        with pytest.raises(ScrapeError):
            scrape_service.validate_public_http_url("example.com/job")

    def test_non_standard_port_rejected(self) -> None:
        with pytest.raises(ScrapeError):
            scrape_service.validate_public_http_url("http://example.com:8080/job")

    def test_empty_url_rejected(self) -> None:
        with pytest.raises(ScrapeError):
            scrape_service.validate_public_http_url("")


class TestBlockedHosts:
    @pytest.mark.parametrize(
        "url",
        [
            "http://localhost/job",
            "http://127.0.0.1/job",
            "http://127.1/job",
            "http://10.0.0.5/job",
            "http://192.168.1.10/job",
            "http://172.16.0.1/job",
            "http://172.31.255.255/job",
            "http://169.254.169.254/latest/meta-data/",
            "http://0.0.0.0/job",
            "http://[::1]/job",
            "https://sub.localhost/job",
            "https://intranet.internal/job",
            "https://printer.lan/job",
        ],
    )
    def test_private_and_internal_blocked(self, url: str) -> None:
        with pytest.raises(ScrapeError) as exc_info:
            scrape_service.validate_public_http_url(url)
        # Safe, non-leaking error message.
        assert "not allowed" in str(exc_info.value) or "blocked" in str(exc_info.value)

    def test_public_ip_literal_allowed(self) -> None:
        assert scrape_service.validate_public_http_url("http://93.184.216.34/job") is not None

    def test_public_domain_allowed(self) -> None:
        # example.com resolves to public addresses.
        assert scrape_service.validate_public_http_url("https://example.com/careers") is not None


class TestDnsRebinding:
    def test_domain_resolving_to_private_ip_blocked(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_getaddrinfo(host, *args, **kwargs):  # noqa: ANN001, ARG002
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.1.2.3", 0))]

        monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
        with pytest.raises(ScrapeError):
            scrape_service.validate_public_http_url("https://evil-rebind.example.com/job")

    def test_unresolvable_domain_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_getaddrinfo(host, *args, **kwargs):  # noqa: ANN001, ARG002
            raise socket.gaierror("name resolution failed")

        monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
        with pytest.raises(ScrapeError):
            scrape_service.validate_public_http_url("https://nonexistent.invalid/job")


class TestRedirectSafety:
    def test_redirect_to_localhost_blocked(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class FakeResponse:
            status_code = 302
            headers = {"Location": "http://127.0.0.1/secret"}

        monkeypatch.setattr(scrape_service.requests, "get", lambda *a, **k: FakeResponse())
        with pytest.raises(ScrapeError):
            scrape_service.fetch_page("https://example.com/job")
