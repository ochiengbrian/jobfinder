"""Unit tests for the AllJobsPo scraper parser."""
from datetime import datetime
from bs4 import BeautifulSoup
import pytest

from scrapers.alljobspo import parse_jobs, parse_date, is_today


# ---------------------------------------------------------------------------
# parse_date
# ---------------------------------------------------------------------------

def test_parse_date_today_keyword():
    assert parse_date("Today") == datetime.now().strftime("%Y-%m-%d")

def test_parse_date_hours_ago():
    assert parse_date("3 hours ago") == datetime.now().strftime("%Y-%m-%d")

def test_parse_date_full_format():
    assert parse_date("01 April 2026") == "2026-04-01"

def test_parse_date_abbreviated_month():
    assert parse_date("15 Apr 2026") == "2026-04-15"

def test_parse_date_iso_format():
    assert parse_date("2026-04-01") == "2026-04-01"

def test_parse_date_empty_returns_none():
    assert parse_date("") is None

def test_parse_date_invalid_returns_none():
    assert parse_date("some random text") is None


# ---------------------------------------------------------------------------
# is_today
# ---------------------------------------------------------------------------

def test_is_today_true():
    assert is_today(datetime.now().strftime("%Y-%m-%d")) is True

def test_is_today_false():
    assert is_today("2020-01-01") is False

def test_is_today_none():
    assert is_today(None) is False


# ---------------------------------------------------------------------------
# parse_jobs — WP Job Manager HTML pattern
# ---------------------------------------------------------------------------

MOCK_HTML_WP = """
<html><body>
  <article class="job_listing">
    <h2><a href="https://www.alljobspo.com/kenya-jobs/software-engineer-techco/">
      Software Engineer
    </a></h2>
    <div class="company">TechCo Ltd</div>
    <div class="location">Mombasa, Kenya</div>
    <time datetime="2026-04-29">April 29, 2026</time>
  </article>
  <article class="job_listing">
    <h2><a href="https://www.alljobspo.com/kenya-jobs/data-analyst-bank/">
      Data Analyst
    </a></h2>
    <div class="company">Equity Bank</div>
    <div class="location">Kenya</div>
    <time datetime="2026-04-28">April 28, 2026</time>
  </article>
</body></html>
"""

def test_parse_jobs_returns_correct_count():
    soup = BeautifulSoup(MOCK_HTML_WP, "html.parser")
    jobs = parse_jobs(soup, "Software Engineering")
    assert len(jobs) == 2

def test_parse_jobs_title():
    soup = BeautifulSoup(MOCK_HTML_WP, "html.parser")
    jobs = parse_jobs(soup, "Software Engineering")
    assert jobs[0]["Job Title"] == "Software Engineer"

def test_parse_jobs_company():
    soup = BeautifulSoup(MOCK_HTML_WP, "html.parser")
    jobs = parse_jobs(soup, "Software Engineering")
    assert jobs[0]["Company"] == "TechCo Ltd"

def test_parse_jobs_location():
    soup = BeautifulSoup(MOCK_HTML_WP, "html.parser")
    jobs = parse_jobs(soup, "Software Engineering")
    assert "Mombasa" in jobs[0]["Location"]

def test_parse_jobs_url_is_absolute():
    soup = BeautifulSoup(MOCK_HTML_WP, "html.parser")
    jobs = parse_jobs(soup, "Software Engineering")
    assert jobs[0]["Job URL"].startswith("https://")

def test_parse_jobs_date_from_datetime_attr():
    soup = BeautifulSoup(MOCK_HTML_WP, "html.parser")
    jobs = parse_jobs(soup, "Software Engineering")
    assert jobs[0]["Date Posted"] == "2026-04-29"

def test_parse_jobs_source_is_alljobspo():
    soup = BeautifulSoup(MOCK_HTML_WP, "html.parser")
    jobs = parse_jobs(soup, "Software Engineering")
    assert all(j["Source"] == "AllJobsPo" for j in jobs)

def test_parse_jobs_empty_html_returns_empty():
    soup = BeautifulSoup("<html><body><p>No results</p></body></html>", "html.parser")
    assert parse_jobs(soup, "Software Engineering") == []
