"""Unit tests for the Cari.co.ke scraper parser."""
from datetime import datetime
from bs4 import BeautifulSoup
import pytest

from scrapers.cari import parse_jobs, parse_date, is_today


# ---------------------------------------------------------------------------
# parse_date
# ---------------------------------------------------------------------------

def test_parse_date_today_keyword():
    assert parse_date("Today") == datetime.now().strftime("%Y-%m-%d")

def test_parse_date_minutes_ago():
    assert parse_date("30 minutes ago") == datetime.now().strftime("%Y-%m-%d")

def test_parse_date_full_date():
    assert parse_date("01 April 2026") == "2026-04-01"

def test_parse_date_slash_format():
    assert parse_date("29/04/2026") == "2026-04-29"

def test_parse_date_iso_format():
    assert parse_date("2026-04-29") == "2026-04-29"

def test_parse_date_empty_returns_none():
    assert parse_date("") is None

def test_parse_date_invalid_returns_none():
    assert parse_date("some text") is None


# ---------------------------------------------------------------------------
# is_today
# ---------------------------------------------------------------------------

def test_is_today_true():
    assert is_today(datetime.now().strftime("%Y-%m-%d")) is True

def test_is_today_false():
    assert is_today("2019-12-31") is False

def test_is_today_none():
    assert is_today(None) is False


# ---------------------------------------------------------------------------
# parse_jobs — classifieds ad HTML pattern
# ---------------------------------------------------------------------------

MOCK_HTML = """
<html><body>
  <div class="listing">
    <h2><a href="https://www.cari.co.ke/jobs/backend-developer-234/">
      Backend Developer
    </a></h2>
    <div class="company">Coastal Systems Ltd</div>
    <div class="location">Mombasa</div>
    <time datetime="2026-04-29">29 April 2026</time>
  </div>
  <div class="listing">
    <h2><a href="https://www.cari.co.ke/jobs/it-officer-567/">
      IT Officer
    </a></h2>
    <div class="company">Port Authority</div>
    <div class="location">Kenya</div>
    <time datetime="2026-04-28">28 April 2026</time>
  </div>
</body></html>
"""

def test_parse_jobs_returns_correct_count():
    soup = BeautifulSoup(MOCK_HTML, "html.parser")
    jobs = parse_jobs(soup, "Backend")
    assert len(jobs) == 2

def test_parse_jobs_title():
    soup = BeautifulSoup(MOCK_HTML, "html.parser")
    jobs = parse_jobs(soup, "Backend")
    assert jobs[0]["Job Title"] == "Backend Developer"

def test_parse_jobs_company():
    soup = BeautifulSoup(MOCK_HTML, "html.parser")
    jobs = parse_jobs(soup, "Backend")
    assert jobs[0]["Company"] == "Coastal Systems Ltd"

def test_parse_jobs_location():
    soup = BeautifulSoup(MOCK_HTML, "html.parser")
    jobs = parse_jobs(soup, "Backend")
    assert jobs[0]["Location"] == "Mombasa"

def test_parse_jobs_url_is_absolute():
    soup = BeautifulSoup(MOCK_HTML, "html.parser")
    jobs = parse_jobs(soup, "Backend")
    assert jobs[0]["Job URL"].startswith("https://")

def test_parse_jobs_date_from_datetime_attr():
    soup = BeautifulSoup(MOCK_HTML, "html.parser")
    jobs = parse_jobs(soup, "Backend")
    assert jobs[0]["Date Posted"] == "2026-04-29"

def test_parse_jobs_source_is_cari():
    soup = BeautifulSoup(MOCK_HTML, "html.parser")
    jobs = parse_jobs(soup, "Backend")
    assert all(j["Source"] == "Cari" for j in jobs)

def test_parse_jobs_empty_html_returns_empty():
    soup = BeautifulSoup("<html><body><p>Nothing here</p></body></html>", "html.parser")
    assert parse_jobs(soup, "Backend") == []

def test_parse_jobs_skips_anchor_with_no_title():
    html = """
    <html><body>
      <div class="listing">
        <a href="https://www.cari.co.ke/jobs/empty/"></a>
        <div class="location">Mombasa</div>
      </div>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    assert parse_jobs(soup, "Backend") == []
