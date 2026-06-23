"""
AllJobsPo Kenya scraper — server-side rendered, uses requests + BeautifulSoup.
Scrapes www.alljobspo.com/kenya-jobs/ for jobs in the configured location.

NOTE: If this scraper returns 0 results after deployment, run debug_new_sites.py
to inspect live HTML and update the CSS selectors in parse_jobs() below.
"""
import logging
import time
import random
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from config import JOB_LOCATION, matches_location

logger = logging.getLogger(__name__)

BASE_URL = "https://www.alljobspo.com"

SEARCH_QUERIES = [
    # Data / Analytics
    ("data scientist",          "Data Science"),
    ("data analyst",            "Data Science"),
    ("data engineer",           "Data Science"),
    # AI / ML
    ("machine learning",        "AI/ML"),
    ("artificial intelligence", "AI/ML"),
    ("AI engineer",             "AI/ML"),
    # Web / Software
    ("frontend",                "Frontend"),
    ("backend",                 "Backend"),
    ("fullstack",               "Fullstack"),
    ("full stack",              "Fullstack"),
    ("software engineer",       "Software Engineering"),
    ("software developer",      "Software Engineering"),
    # Cloud / DevOps
    ("DevOps",                  "Cloud/DevOps"),
    ("cloud engineer",          "Cloud/DevOps"),
    ("AWS",                     "Cloud/DevOps"),
    ("Azure",                   "Cloud/DevOps"),
    # Security
    ("cybersecurity",           "Cybersecurity"),
    ("information security",    "Cybersecurity"),
    # ICT / IT
    ("ICT officer",             "ICT"),
    ("IT officer",              "IT"),
    ("systems administrator",   "IT"),
    ("network engineer",        "IT"),
    # Database
    ("database administrator",  "Database"),
    ("database developer",      "Database"),
    # NGO / Development sector
    ("program officer",         "NGO"),
    ("project officer",         "NGO"),
    ("field officer",           "NGO"),
    ("monitoring evaluation",   "NGO"),
    ("community development",   "NGO"),
    ("humanitarian",            "NGO"),
    ("NGO",                     "NGO"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def parse_date(date_text: str) -> str | None:
    """
    Parse date strings from AllJobsPo. Tries multiple common formats.
    Returns YYYY-MM-DD or None if unparseable.
    """
    date_text = date_text.strip()
    if not date_text:
        return None
    today = datetime.now().strftime("%Y-%m-%d")
    text = date_text.lower()
    if any(kw in text for kw in ("today", "just now", "minute", "hour", "1 day ago")):
        return today
    current_year = datetime.now().year
    for fmt in ("%d %B %Y", "%d %B", "%d %b %Y", "%d %b", "%B %d, %Y", "%Y-%m-%d"):
        try:
            if "%Y" not in fmt:
                parsed = datetime.strptime(f"{date_text} {current_year}", f"{fmt} %Y")
            else:
                parsed = datetime.strptime(date_text, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def is_today(date_str: str | None) -> bool:
    if not date_str:
        return False
    return date_str == datetime.now().strftime("%Y-%m-%d")


def fetch_page(query: str, page: int = 1) -> BeautifulSoup | None:
    """Fetch a search results page from AllJobsPo."""
    if page == 1:
        url = f"{BASE_URL}/kenya-jobs/?s={requests.utils.quote(query)}"
    else:
        url = f"{BASE_URL}/kenya-jobs/page/{page}/?s={requests.utils.quote(query)}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        logger.error(f"AllJobsPo fetch error for '{query}' page {page}: {e}")
        return None


def parse_jobs(soup: BeautifulSoup, category: str) -> list[dict]:
    """
    Parse job listings from an AllJobsPo search results page.
    Tries multiple common WordPress job board HTML patterns.
    """
    jobs = []

    # Pattern 1: <article class="job_listing"> (WP Job Manager plugin)
    articles = soup.find_all("article", class_=lambda c: c and "job" in c)

    # Pattern 2: <li class="job_listing"> fallback
    if not articles:
        articles = soup.find_all("li", class_=lambda c: c and "job" in c)

    # Pattern 3: generic .jobs-list-item or .job-item
    if not articles:
        articles = soup.find_all(class_=lambda c: c and ("job-item" in c or "job_listing" in c))

    for article in articles:
        # Title & URL
        link_tag = article.find("a", href=True)
        if not link_tag:
            continue
        title_el = article.find(["h2", "h3", "h4"]) or link_tag
        title = title_el.get_text(strip=True)
        job_url = link_tag["href"]
        if not job_url.startswith("http"):
            job_url = BASE_URL + job_url

        # Company
        company_el = article.find(class_=lambda c: c and "company" in c)
        company = company_el.get_text(strip=True) if company_el else ""

        # Location
        location_el = article.find(class_=lambda c: c and "location" in c)
        location = location_el.get_text(strip=True) if location_el else "Kenya"

        # Date
        date_el = (
            article.find("time")
            or article.find(class_=lambda c: c and "date" in c)
        )
        date_text = ""
        if date_el:
            date_text = date_el.get("datetime") or date_el.get_text(strip=True)
        date_str = parse_date(date_text)

        jobs.append({
            "Job Title": title,
            "Company": company,
            "Location": location,
            "Category": category,
            "Source": "AllJobsPo",
            "Job URL": job_url,
            "Date Posted": date_str or "",
            "_date": date_str,
            "_location": location,
        })

    return jobs


def scrape(today_only: bool = True) -> list[dict]:
    """Scrape AllJobsPo Kenya for all target job categories."""
    all_jobs = []
    seen_urls = set()

    for query, category in SEARCH_QUERIES:
        logger.info(f"AllJobsPo: searching '{query}'...")
        page = 1

        while True:
            soup = fetch_page(query, page)
            if not soup:
                break

            jobs = parse_jobs(soup, category)
            if not jobs:
                break

            found_today = False
            for job in jobs:
                if job["Job URL"] in seen_urls:
                    continue
                if today_only and not is_today(job["_date"]):
                    continue
                if not matches_location(job["_location"]):
                    continue
                seen_urls.add(job["Job URL"])
                job.pop("_date", None)
                job.pop("_location", None)
                all_jobs.append(job)
                found_today = True

            if today_only and not found_today:
                break

            # Check for next page link
            next_link = (
                soup.find("a", class_="next")
                or soup.find("a", string=lambda t: t and ("next" in t.lower() or "»" in t))
            )
            if not next_link:
                break

            page += 1
            time.sleep(random.uniform(1, 3))

        time.sleep(random.uniform(1, 2))

    logger.info(f"AllJobsPo: found {len(all_jobs)} new job(s) today.")
    return all_jobs
