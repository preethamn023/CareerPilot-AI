"""Safe job-description scraping: URL validation (SSRF hardening),
fetching and HTML-to-text extraction. Purely deterministic - no AI here.

Security measures implemented:
- Only http/https schemes.
- localhost / *.localhost / *.local / *.internal hostnames rejected.
- IP literals and DNS-resolved addresses are checked against
  loopback, private, link-local (incl. cloud metadata 169.254.169.254),
  reserved and multicast ranges.
- Only ports 80 / 443 (or scheme defaults) are allowed.
- Redirects are followed manually and every hop is re-validated.
- Response size and timeouts are capped; only text/html is accepted.
"""
from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.config import settings
from app.services.exceptions import ScrapeError

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {80, 443}
MIN_JOB_TEXT_CHARS = 200
MAX_TEXT_CHARS = 24_000

_BLOCKED_HOSTNAME_SUFFIXES = (".localhost", ".local", ".internal", ".lan", ".home.arpa")

_STRIP_TAGS = (
    "script", "style", "noscript", "iframe", "svg", "canvas", "form",
    "button", "input", "select", "textarea", "template",
)
_STRIP_ROLES = ("navigation", "banner", "contentinfo", "complementary", "search", "menubar")
_STRIP_TAGNAMES = ("nav", "header", "footer", "aside", "form")


@dataclass
class FetchedPage:
    url: str
    final_url: str
    html: str
    title: str | None
    meta_description: str | None


@dataclass
class CleanedJobContent:
    title: str | None
    meta_description: str | None
    text: str
    char_count: int


def _resolve_host(hostname: str) -> list[str]:
    """Resolve a hostname to all its IP addresses (A/AAAA)."""
    try:
        infos = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ScrapeError(f"Could not resolve the domain '{hostname}'. Please check the URL.") from exc
    return list({info[4][0] for info in infos})


def _is_public_ip(ip_text: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_text)
    except ValueError:
        return False
    return (
        not ip.is_private
        and not ip.is_loopback
        and not ip.is_link_local
        and not ip.is_reserved
        and not ip.is_multicast
        and not ip.is_unspecified
    )


def validate_public_http_url(url: str) -> str:
    """Validate that a URL is an acceptable public http(s) target.

    Returns the normalised URL string; raises ScrapeError otherwise.
    """
    if not url or not url.strip():
        raise ScrapeError("Please provide a job description URL.")
    url = url.strip()

    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise ScrapeError("Only http:// and https:// URLs are supported.")

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise ScrapeError("The URL does not contain a valid domain name.")

    if hostname == "localhost" or hostname.endswith(_BLOCKED_HOSTNAME_SUFFIXES):
        raise ScrapeError("Local and internal hostnames are not allowed.")

    if parsed.port is not None and parsed.port not in ALLOWED_PORTS:
        raise ScrapeError("Only ports 80 and 443 are supported for job URLs.")

    # Check IP literal or DNS resolution.
    try:
        ipaddress.ip_address(hostname)
        candidates = [hostname]
    except ValueError:
        try:
            # Handle shorthand IPv4 notation like '127.1' (common SSRF bypass attempt)
            if hostname and all(part.isdigit() for part in hostname.split(".")):
                candidates = [socket.inet_ntoa(socket.inet_aton(hostname))]
            else:
                candidates = _resolve_host(hostname)
        except (OSError, ValueError):
            candidates = _resolve_host(hostname)

    for ip_text in candidates:
        if not _is_public_ip(ip_text):
            raise ScrapeError(
                "This URL points to a private or internal network address, which is blocked for security reasons."
            )
    return url


def _fetch_single(url: str) -> requests.Response:
    return requests.get(  # noqa: S113 - timeout is set explicitly below
        url,
        timeout=settings.scrape_timeout_seconds,
        allow_redirects=False,
        stream=True,
        headers={
            "User-Agent": settings.scrape_user_agent,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )


def fetch_page(url: str) -> FetchedPage:
    """Fetch a validated URL, following at most `max_redirects` hops with
    re-validation of every hop."""
    current = validate_public_http_url(url)
    visited = 0

    while True:
        try:
            response = _fetch_single(current)
        except requests.Timeout as exc:
            raise ScrapeError(f"The website timed out after {settings.scrape_timeout_seconds}s. Please try again or paste the job description manually.") from exc
        except requests.RequestException as exc:
            raise ScrapeError("Could not connect to the website. It may be down or blocking automated access - please paste the job description manually.") from exc

        if response.status_code in (301, 302, 303, 307, 308):
            visited += 1
            if visited > settings.max_redirects:
                raise ScrapeError("Too many redirects while fetching the page.")
            location = response.headers.get("Location", "")
            if not location:
                raise ScrapeError("The website returned an invalid redirect.")
            # Resolve relative redirects safely.
            from urllib.parse import urljoin

            current = urljoin(current, location)
            validate_public_http_url(current)
            continue

        if response.status_code == 403 or response.status_code == 401:
            raise ScrapeError(
                "The website is blocking automated access (CAPTCHA, login or bot protection). "
                "Please paste the job description text manually."
            )
        if response.status_code == 404:
            raise ScrapeError("The page was not found (404). Please check the URL.")
        if response.status_code >= 400:
            raise ScrapeError(f"The website returned HTTP {response.status_code}. Please paste the job description manually.")

        content_type = (response.headers.get("Content-Type") or "").lower()
        if "text/html" not in content_type and "xhtml" not in content_type:
            raise ScrapeError("The URL did not return a web page (unsupported content type). Please paste the job description manually.")

        # Read with a hard size cap.
        chunks: list[bytes] = []
        total = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            total += len(chunk)
            if total > settings.max_content_bytes:
                raise ScrapeError("The page is too large to process. Please paste the job description manually.")
            chunks.append(chunk)
        html = b"".join(chunks).decode("utf-8", errors="replace")

        soup = BeautifulSoup(html, "lxml")
        title_tag = soup.find("title")
        og_title = soup.find("meta", attrs={"property": "og:title"})
        meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})

        return FetchedPage(
            url=url,
            final_url=current,
            html=html,
            title=(og_title.get("content") if og_title and og_title.get("content") else (title_tag.get_text(strip=True) if title_tag else None)),
            meta_description=(meta_desc.get("content") if meta_desc and meta_desc.get("content") else None),
        )


def extract_job_text(html: str) -> CleanedJobContent:
    """Convert job-page HTML to clean, meaningful text by removing
    navigation, scripts, ads and boilerplate."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup.find_all(_STRIP_TAGS):
        tag.decompose()

    for tag in soup.find_all(_STRIP_TAGNAMES):
        tag.decompose()

    for tag in soup.find_all(attrs={"role": _STRIP_ROLES}):
        tag.decompose()

    # Heuristic removal of ad / cookie / menu containers.
    for attr in ("class", "id"):
        for tag in soup.find_all(attrs={attr: True}):
            tokens = " ".join(tag[attr]).lower() if isinstance(tag[attr], list) else str(tag[attr]).lower()
            if any(key in tokens for key in ("nav", "menu", "footer", "header", "sidebar", "advert", "cookie", "banner", "social", "comment", "popup", "modal")):
                tag.decompose()

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    # Prefer semantic main content containers.
    root = (
        soup.find("main")
        or soup.find(attrs={"role": "main"})
        or soup.find("article")
        or soup.body
        or soup
    )

    text = root.get_text("\n")
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    # De-duplicate consecutive repeated lines (menus repeated by JS).
    deduped: list[str] = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)

    cleaned = "\n".join(deduped)[:MAX_TEXT_CHARS]
    return CleanedJobContent(
        title=title,
        meta_description=None,
        text=cleaned,
        char_count=len(cleaned),
    )


def scrape_job_description(url: str) -> tuple[FetchedPage, CleanedJobContent]:
    """Full pipeline: validate -> fetch -> clean. Raises ScrapeError when
    the page cannot be turned into meaningful job text."""
    page = fetch_page(url)
    cleaned = extract_job_text(page.html)
    if cleaned.char_count < MIN_JOB_TEXT_CHARS:
        raise ScrapeError(
            "Could not extract meaningful job-description content from this page "
            "(it may rely on JavaScript rendering). Please paste the job description text manually."
        )
    return page, cleaned
