"""Tests: HTML-to-text job description extraction (Module B)."""
from __future__ import annotations

from app.services import scrape_service

JD_HTML = """
<!DOCTYPE html>
<html>
<head><title>Software Engineer at CloudPay - Careers</title>
<meta name="description" content="Apply for Software Engineer role"></head>
<body>
<nav class="main-nav"><a href="/">Home</a><a href="/jobs">Jobs</a></nav>
<header><div class="banner-ad">BUY NOW 50% OFF</div></header>
<script>window.tracking = {id: 42};</script>
<style>.nav { color: red; }</style>
<main>
  <h1>Software Engineer (Fresher)</h1>
  <p>Company: CloudPay Solutions, Bengaluru</p>
  <h2>Responsibilities</h2>
  <ul>
    <li>Develop and maintain web applications using Python and Django or Flask</li>
    <li>Build responsive user interfaces with React</li>
    <li>Deploy and operate services using Docker and basic AWS</li>
  </ul>
  <h2>Requirements</h2>
  <ul>
    <li>B.Tech / MCA / BCA in Computer Science</li>
    <li>0-2 years of experience</li>
    <li>Python, JavaScript, SQL databases, Git version control</li>
  </ul>
</main>
<aside class="sidebar"><div class="advert">Related jobs you may like</div></aside>
<footer><div class="cookie-banner">We use cookies</div>Copyright CloudPay</footer>
<form><input placeholder="search jobs"></form>
</body>
</html>
"""


def test_extracts_main_content() -> None:
    cleaned = scrape_service.extract_job_text(JD_HTML)
    assert "Software Engineer (Fresher)" in cleaned.text
    assert "Python and Django" in cleaned.text
    assert "0-2 years of experience" in cleaned.text


def test_removes_scripts_styles_and_tracking() -> None:
    cleaned = scrape_service.extract_job_text(JD_HTML)
    assert "window.tracking" not in cleaned.text
    assert "color: red" not in cleaned.text


def test_removes_navigation_and_ads() -> None:
    cleaned = scrape_service.extract_job_text(JD_HTML)
    assert "BUY NOW" not in cleaned.text
    assert "We use cookies" not in cleaned.text
    assert "Related jobs" not in cleaned.text


def test_title_extracted() -> None:
    cleaned = scrape_service.extract_job_text(JD_HTML)
    assert cleaned.title is not None
    assert "CloudPay" in cleaned.title


def test_full_scrape_pipeline_with_mocked_fetch(monkeypatch) -> None:  # noqa: ANN001
    class FakeResponse:
        status_code = 200
        headers = {"Content-Type": "text/html; charset=utf-8"}

        def iter_content(self, chunk_size: int = 8192):  # noqa: ARG002
            yield JD_HTML.encode("utf-8")

    def fake_get(url, **kwargs):  # noqa: ANN001, ARG001
        assert url == "https://example.com/job/1"
        return FakeResponse()

    monkeypatch.setattr(scrape_service.requests, "get", fake_get)
    page, cleaned = scrape_service.scrape_job_description("https://example.com/job/1")
    assert "Software Engineer" in cleaned.text
    assert page.final_url == "https://example.com/job/1"


def test_thin_page_raises_helpful_error(monkeypatch) -> None:  # noqa: ANN001
    class FakeResponse:
        status_code = 200
        headers = {"Content-Type": "text/html"}

        def iter_content(self, chunk_size: int = 8192):  # noqa: ARG002
            yield b"<html><body>JS app</body></html>"

    monkeypatch.setattr(scrape_service.requests, "get", lambda *a, **k: FakeResponse())
    try:
        scrape_service.scrape_job_description("https://example.com/job/2")
        raise AssertionError("expected ScrapeError")
    except scrape_service.ScrapeError as exc:
        assert "paste" in str(exc).lower() or "manually" in str(exc).lower()
