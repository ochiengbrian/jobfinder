# Job Finder — Mombasa & Coast Region Job Tracker

An autonomous system that scrapes tech job postings from multiple Kenyan job boards every 2 hours,
saves them to Google Sheets, and sends each new job as a WhatsApp message to your group.
Runs via GitHub Actions with zero manual intervention required after setup.

---

## What It Does

- Scrapes **7 job boards** every 2 hours via GitHub Actions
- Filters for tech jobs in **Mombasa / Coast Province** by default (configurable)
- Saves new jobs to a **Google Sheet** (deduplicates — no repeats ever)
- Sends each new job as a **WhatsApp message** to your group via Green API
- Commits a run log to `activity_log.md` after each run

---

## Target Job Categories

| Category | Search Terms |
|----------|-------------|
| Data Science | Data Scientist, Data Analyst |
| AI / Machine Learning | Machine Learning, AI Engineer |
| Frontend | Frontend Developer |
| Fullstack | Fullstack Developer, Full Stack Developer |
| Software Engineering | Software Engineer |
| Backend | Backend Developer |
| Cloud / DevOps | Cloud Engineer, DevOps |
| Cybersecurity | Cybersecurity |
| ICT / IT | ICT, IT, Computer Science, Computer, Database |

---

## Job Sources

| Site | Method | Notes |
|------|--------|-------|
| [MyJobMag](https://www.myjobmag.co.ke) | requests + BeautifulSoup | Kenya-wide, location-filtered |
| [JobWebKenya](https://jobwebkenya.com) | requests + BeautifulSoup | Kenya-wide, location-filtered |
| [BrighterMonday](https://www.brightermonday.co.ke) | Playwright (headless browser) | Location param in URL |
| [LinkedIn](https://www.linkedin.com/jobs) | Playwright (headless browser) | Location param in URL |
| [Jobrapido](https://ke.jobrapido.com) | Playwright (headless browser) | Location param in URL |
| [AllJobsPo](https://www.alljobspo.com/kenya-jobs/) | requests + BeautifulSoup | Kenya-wide, location-filtered |
| [Cari](https://www.cari.co.ke) | requests + BeautifulSoup | Location param in URL |

---

## Google Sheet Columns

| Column | Description |
|--------|-------------|
| Date Found | Date the job was scraped |
| Job Title | Position name |
| Company | Employer name |
| Location | City/region or "Kenya" if unspecified |
| Category | Data Science / AI/ML / Frontend / etc. |
| Source | Which job board it came from |
| Job URL | Direct link to the job listing |
| Date Posted | Date the job was posted on the site |

---

## WhatsApp Message Format

Each new job is sent as a separate message:

```
*Job Title:* Senior Data Scientist
*Company:* Safaricom PLC
*Location:* Mombasa
*Link to the job:* https://...
```

---

## Project Structure

```
job-finder/
├── .github/
│   └── workflows/
│       └── job_scraper.yml       # GitHub Actions — runs every 2 hours
├── scrapers/
│   ├── __init__.py
│   ├── myjobmag.py               # MyJobMag scraper
│   ├── jobwebkenya.py            # JobWebKenya scraper
│   ├── brighter_monday.py        # BrighterMonday scraper (Playwright)
│   ├── linkedin.py               # LinkedIn scraper (Playwright)
│   ├── jobrapido.py              # Jobrapido Kenya scraper (Playwright)
│   ├── alljobspo.py              # AllJobsPo Kenya scraper
│   └── cari.py                   # Cari.co.ke scraper
├── tests/
│   ├── test_sheets.py
│   ├── test_myjobmag.py
│   ├── test_jobwebkenya.py
│   └── test_brighter_monday.py
├── config.py                     # Shared location config + matches_location()
├── main.py                       # Pipeline entry point
├── sheets_client.py              # Google Sheets read/write/deduplicate
├── whatsapp_notifier.py          # WhatsApp notifications via Green API
├── requirements.txt              # Python dependencies
├── .env.example                  # Template for local environment variables
└── activity_log.md               # Auto-updated run log (committed by Actions)
```

---

## Local Development Setup

```bash
# 1. Clone your repo
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd job-finder

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browser
playwright install chromium

# 5. Set up environment variables
cp .env.example .env
# Fill in your values in .env

# 6. Run the pipeline
python main.py

# 7. Run tests
pytest tests/ -v
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_SHEET_ID` | ID from your Google Sheet URL |
| `GOOGLE_CREDENTIALS_JSON` | Path to service account JSON (local) or full JSON contents (GitHub Actions) |
| `GREEN_API_INSTANCE_ID` | Your Green API instance ID |
| `GREEN_API_TOKEN` | Your Green API token |
| `WHATSAPP_GROUP_CHAT_ID` | Your WhatsApp group chat ID — format: `XXXXXXXXXX@g.us` |
| `JOB_LOCATION` | Location to filter jobs. Default: `Mombasa`. Set to `Kenya` for all of Kenya. |

---

## GitHub Actions Secrets Required

Add these in your repo under **Settings → Secrets and variables → Actions**:

| Secret | Description |
|--------|-------------|
| `GOOGLE_SHEET_ID` | Your Google Sheet ID |
| `GOOGLE_CREDENTIALS_JSON` | Contents of your service account JSON file |
| `GREEN_API_INSTANCE_ID` | Green API instance ID |
| `GREEN_API_TOKEN` | Green API token |
| `WHATSAPP_GROUP_CHAT_ID` | WhatsApp group chat ID |
| `JOB_LOCATION` | `Mombasa` (or whatever city you want — omit to use the default) |
| `GIT_USER_NAME` | Your name — used for the activity log git commit |
| `GIT_USER_EMAIL` | Your email — used for the activity log git commit |

---

## Schedule

Runs automatically **every 2 hours** via GitHub Actions cron: `0 */2 * * *`

To trigger a manual run: **GitHub → Actions → Daily Job Scraper → Run workflow**

---

## Changing the Target Location

To change from Mombasa to another city:

1. Go to your GitHub repo → **Settings → Secrets and variables → Actions**
2. Edit the `JOB_LOCATION` secret to e.g. `Nairobi`, `Kisumu`, or `Kenya` (for all of Kenya)
3. The next run will use the new location automatically

For local development, edit `JOB_LOCATION=` in your `.env` file.

---

## Adding a New Job Category

1. Add a new search query tuple to `SEARCH_QUERIES` in each scraper:
   ```python
   ("network engineer", "Networking"),
   ```
2. Push to `main` — the next scheduled run includes it automatically.

## Adding a New Job Site

1. Create `scrapers/newsite.py` following the same pattern as existing scrapers
2. Import and add it to the `scrapers` list in `main.py`
3. Push to `main`
