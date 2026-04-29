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
JOB_LOCATION = os.environ.get("JOB_LOCATION", "Mombasa")


def matches_location(location_text: str) -> bool:
    """
    Returns True if a job's location is compatible with JOB_LOCATION.

    Rules:
    - If JOB_LOCATION is "Kenya", include everything.
    - Jobs tagged "Kenya", "Remote", "Anywhere", or with no city are always included
      (they are nationwide/unspecified roles that may be relevant anywhere).
    - Otherwise, include only if the job location contains the target city/region.
    - For Mombasa, also match the other Coast Province counties.
    """
    if not location_text:
        return True

    loc = location_text.lower().strip()
    target = JOB_LOCATION.lower().strip()

    # Searching all Kenya — include everything
    if target == "kenya":
        return True

    # Nationwide / unspecified roles are always included
    if any(kw in loc for kw in ("kenya", "remote", "anywhere", "nationwide")):
        return True

    # Direct substring match (e.g. "Mombasa CBD" matches target "mombasa")
    if target in loc or loc in target:
        return True

    # For Mombasa, also include all Coast Province counties
    if target == "mombasa":
        coast_keywords = ["coast", "kilifi", "kwale", "lamu", "malindi", "tana river", "taita"]
        if any(kw in loc for kw in coast_keywords):
            return True

    return False
