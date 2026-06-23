"""
Jobrapido Kenya scraper — JavaScript-rendered, uses Playwright headless browser.
Searches ke.jobrapido.com for jobs in the configured location.

NOTE: If this scraper returns 0 results after deployment, the site's HTML
selectors may have changed. Run debug_new_sites.py to inspect live HTML
and update the evaluate() selector list below.
"""
import logging
import time
import random
from datetime import datetime

from config import JOB_LOCATION, matches_location

logger = logging.getLogger(__name__)

BASE_URL = "https://ke.jobrapido.com"

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

MAX_PAGES = 2
RESULTS_PER_PAGE = 20


def parse_relative_date(date_text: str) -> str | None:
    """Parse Jobrapido relative date strings into YYYY-MM-DD. Returns today for recent postings."""
    today = datetime.now().strftime("%Y-%m-%d")
    text = date_text.strip().lower()
    if not text:
        return None
    if any(kw in text for kw in ("today", "just now", "minute", "hour", "1 day ago")):
        return today
    return None


def scrape_query(page, query: str, category: str, seen_urls: set, today_only: bool = True) -> list[dict]:
    """Scrape a single search query on Jobrapido using an open Playwright page."""
    jobs = []
    today = datetime.now().strftime("%Y-%m-%d")
    location_param = JOB_LOCATION.replace(" ", "+")

    for page_num in range(1, MAX_PAGES + 1):
        start = (page_num - 1) * RESULTS_PER_PAGE
        if page_num == 1:
            url = f"{BASE_URL}/?q={query.replace(' ', '+')}&l={location_param}"
        else:
            url = f"{BASE_URL}/?q={query.replace(' ', '+')}&l={location_param}&start={start}"

        try:
            page.goto(url, wait_until="networkidle", timeout=45000)
        except Exception as e:
            logger.warning(f"Jobrapido: page load issue for '{query}' page {page_num}: {e}")
            break

        # Wait for any job result container to appear
        try:
            page.wait_for_selector(
                "div.result, article.job, li.job, div[class*='job-card'], div[class*='result']",
                timeout=15000,
            )
        except Exception:
            logger.info(f"Jobrapido: no listings found for '{query}' page {page_num}")
            break

        cards_data = page.evaluate("""() => {
            // Jobrapido uses div.result as the job card container
            const selectors = [
                'div.result',
                'article.job',
                'li.job',
                'div[class*="job-card"]',
                'div[class*="result-item"]',
            ];
            let cards = [];
            for (const sel of selectors) {
                const found = document.querySelectorAll(sel);
                if (found.length > 0) { cards = Array.from(found); break; }
            }

            return cards.map(card => {
                // Title + URL
                const titleEl = card.querySelector('h2 a, h3 a, a[class*="title"], a[class*="job-title"]');
                const title = titleEl ? titleEl.innerText.trim() : '';
                let url = titleEl ? (titleEl.getAttribute('href') || '') : '';

                // Company
                const companyEl = card.querySelector(
                    '[class*="company"], [class*="employer"], [class*="recruiter"]'
                );
                const company = companyEl ? companyEl.innerText.trim() : '';

                // Location
                const locationEl = card.querySelector(
                    '[class*="location"], [class*="city"], span.where'
                );
                const location = locationEl ? locationEl.innerText.trim() : '';

                // Date
                const dateEl = card.querySelector('time, [class*="date"], [class*="posted"]');
                const dateText = dateEl
                    ? (dateEl.getAttribute('datetime') || dateEl.innerText.trim())
                    : '';

                return { title, url, company, location, dateText };
            }).filter(j => j.title);
        }""")

        if not cards_data:
            break

        found_today = False
        for item in cards_data:
            job_url = item["url"]
            if not job_url:
                continue
            if not job_url.startswith("http"):
                job_url = BASE_URL + job_url
            if job_url in seen_urls:
                continue
            if not matches_location(item.get("location", "")):
                continue

            date_str = parse_relative_date(item.get("dateText", ""))
            if today_only and not date_str:
                continue

            jobs.append({
                "Job Title": item["title"],
                "Company": item["company"],
                "Location": item["location"] or JOB_LOCATION,
                "Category": category,
                "Source": "Jobrapido",
                "Job URL": job_url,
                "Date Posted": date_str or today,
            })
            seen_urls.add(job_url)
            found_today = True

        if today_only and not found_today:
            break

        time.sleep(random.uniform(1, 2))

    return jobs


def scrape(today_only: bool = True) -> list[dict]:
    """Scrape Jobrapido Kenya for all target job categories using Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright is not installed. Run: playwright install chromium")
        return []

    all_jobs = []
    seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        for query, category in SEARCH_QUERIES:
            logger.info(f"Jobrapido: searching '{query}'...")
            jobs = scrape_query(page, query, category, seen_urls, today_only)
            all_jobs.extend(jobs)
            logger.info(f"Jobrapido: '{query}' → {len(jobs)} job(s)")
            time.sleep(random.uniform(2, 3))

        browser.close()

    logger.info(f"Jobrapido: found {len(all_jobs)} total job(s).")
    return all_jobs
