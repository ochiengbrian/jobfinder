"""
Shared configuration — imported by all scrapers.

To change the target job location, set JOB_LOCATION in your .env file
or as a GitHub Actions Secret. Default is Mombasa (Coast Province, Kenya).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Default: Mombasa (Coast Province, Kenya)
# Examples: "Nairobi", "Kisumu", "Nakuru", "Kenya" (for all of Kenya)
JOB_LOCATION = os.environ.get("JOB_LOCATION", "Kenya")


def matches_location(location_text: str) -> bool:
    """
    Returns True if a job's location is compatible with JOB_LOCATION.

    Rules:
    - Empty / no location: always included (truly unspecified).
    - If JOB_LOCATION is "Kenya": include everything.
    - Remote / hybrid / work-from-anywhere: always included.
    - Jobs tagged "Kenya" on a board: EXCLUDED when target is a specific city.
      These are almost always Nairobi-based jobs listed broadly — they are NOT
      nationwide opportunities. Set JOB_LOCATION=Kenya to include them.
    - Otherwise: only jobs whose location matches the target city/region.
    - For Mombasa: also matches Coast Province counties (Kilifi, Kwale, Lamu…).
    """
    if not location_text or not location_text.strip():
        return True  # Truly unspecified — could be anywhere

    loc = location_text.lower().strip()
    target = JOB_LOCATION.lower().strip()

    # If searching all Kenya, include everything
    if target == "kenya":
        return True

    # Remote / hybrid jobs can be done from any location
    if any(kw in loc for kw in ("remote", "hybrid", "anywhere", "work from home", "wfh")):
        return True

    # Direct substring match (e.g. "Mombasa CBD" matches target "mombasa")
    if target in loc or loc in target:
        return True

    # For Mombasa, also match Coast Province counties
    if target == "kenya" or target == "mombasa":
        coast_keywords = ["nairobi", "mombasa", "coast", "kilifi", "kwale", "lamu", "malindi", "tana river", "taita"]
        if any(kw in loc for kw in coast_keywords):
            return True

    return False


# ---------------------------------------------------------------------------
# Title relevance filter — applied in main.py after scraping
# ---------------------------------------------------------------------------

_RELEVANT_TITLE_KEYWORDS = [
    # Roles
    "engineer", "developer", "programmer", "architect", "scientist",
    "analyst", "administrator", "technician", "specialist",
    # Domains
    "software", "frontend", "backend", "fullstack", "full stack", "full-stack",
    "data science", "machine learning", "artificial intelligence",
    "cybersecurity", "cyber security", "information security",
    "devops", "cloud", "network", "database", "sysadmin",
    # IT-specific phrases (avoid matching bare "it" as substring in other words)
    "it officer", "ict officer", "it manager", "ict manager",
    "it support", "it director", "it specialist", "ict specialist",
    "it technician", "ict technician",
    "information systems", "information technology",
    # Tech stacks / platforms
    "web", "mobile", "android", "ios", "react", "python", "java",
    "aws", "azure", "gcp", "linux", "computer",
    # NGO / Development sector
    "ngo", "program officer", "project officer", "field officer",
    "monitoring", "evaluation", "community development",
    "humanitarian", "grants", "fundraising", "development officer",
]

# Keep the old name as an alias so existing imports and tests don't break
_TECH_TITLE_KEYWORDS = _RELEVANT_TITLE_KEYWORDS


def is_tech_job(job_title: str) -> bool:
    """
    Returns True if the job title is relevant (tech or NGO/development sector).
    Used to filter out irrelevant jobs that slip through keyword searches
    because job boards match against full descriptions, not just titles.
    """
    title = job_title.lower()
    return any(kw in title for kw in _RELEVANT_TITLE_KEYWORDS)
