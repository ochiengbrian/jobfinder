"""
Pipeline resilience tests — verify that main.run() keeps going when one or
more scrapers fail, and that results from working scrapers are still saved.

Patching strategy: patch each scraper at its source module path
(e.g. "scrapers.myjobmag.scrape") so main.py picks up the mock at call time.
"""
from unittest.mock import patch, MagicMock, call
import pytest

import main


GOOD_JOB = {
    "Job Title": "Software Engineer",
    "Company": "Acme Ltd",
    "Location": "Mombasa",
    "Category": "Software Engineering",
    "Source": "JobWebKenya",
    "Job URL": "https://jobwebkenya.com/jobs/sw-eng-acme",
    "Date Posted": "2026-04-29",
}

# Helper: patch all 7 scrapers at once with safe defaults (return [])
# Pass keyword overrides as side_effect= or return_value= dicts per scraper name.
_SCRAPER_PATHS = [
    "scrapers.myjobmag.scrape",
    "scrapers.jobwebkenya.scrape",
    "scrapers.brighter_monday.scrape",
    "scrapers.linkedin.scrape",
    "scrapers.jobrapido.scrape",
    "scrapers.alljobspo.scrape",
    "scrapers.cari.scrape",
]


# ---------------------------------------------------------------------------
# Resilience: one scraper crashes, others still run
# ---------------------------------------------------------------------------

def test_pipeline_continues_when_one_scraper_raises():
    """A scraper that raises must not stop the rest of the pipeline."""
    with patch("scrapers.myjobmag.scrape", side_effect=RuntimeError("site is down")), \
         patch("scrapers.jobwebkenya.scrape", return_value=[GOOD_JOB]), \
         patch("scrapers.brighter_monday.scrape", return_value=[]), \
         patch("scrapers.linkedin.scrape", return_value=[]), \
         patch("scrapers.jobrapido.scrape", return_value=[]), \
         patch("scrapers.alljobspo.scrape", return_value=[]), \
         patch("scrapers.cari.scrape", return_value=[]), \
         patch("main.sheets_client.save_jobs", return_value=(1, [GOOD_JOB])), \
         patch("main.whatsapp_notifier.send_jobs_to_whatsapp", return_value=1), \
         patch("main._append_activity_log"):
        main.run()  # must not raise


def test_pipeline_saves_jobs_from_working_scrapers():
    """Jobs from working scrapers are saved even when another scraper fails."""
    with patch("scrapers.myjobmag.scrape", return_value=[GOOD_JOB]), \
         patch("scrapers.jobwebkenya.scrape", return_value=[]), \
         patch("scrapers.brighter_monday.scrape", side_effect=ConnectionError("timeout")), \
         patch("scrapers.linkedin.scrape", return_value=[]), \
         patch("scrapers.jobrapido.scrape", return_value=[]), \
         patch("scrapers.alljobspo.scrape", return_value=[]), \
         patch("scrapers.cari.scrape", return_value=[]), \
         patch("main.sheets_client.save_jobs", return_value=(1, [GOOD_JOB])) as mock_save, \
         patch("main.whatsapp_notifier.send_jobs_to_whatsapp", return_value=1), \
         patch("main._append_activity_log"):
        main.run()

    mock_save.assert_called_once()
    saved_jobs = mock_save.call_args[0][0]
    assert len(saved_jobs) == 1
    assert saved_jobs[0]["Job Title"] == "Software Engineer"


def test_pipeline_continues_when_all_scrapers_fail():
    """If every scraper fails, run() logs errors and exits cleanly — no crash."""
    with patch("scrapers.myjobmag.scrape", side_effect=RuntimeError("down")), \
         patch("scrapers.jobwebkenya.scrape", side_effect=RuntimeError("down")), \
         patch("scrapers.brighter_monday.scrape", side_effect=RuntimeError("down")), \
         patch("scrapers.linkedin.scrape", side_effect=RuntimeError("down")), \
         patch("scrapers.jobrapido.scrape", side_effect=RuntimeError("down")), \
         patch("scrapers.alljobspo.scrape", side_effect=RuntimeError("down")), \
         patch("scrapers.cari.scrape", side_effect=RuntimeError("down")), \
         patch("main.sheets_client.save_jobs") as mock_save, \
         patch("main.whatsapp_notifier.send_jobs_to_whatsapp"), \
         patch("main._append_activity_log"):
        main.run()  # must not raise

    mock_save.assert_not_called()


def test_pipeline_continues_when_multiple_scrapers_fail():
    """Three failing scrapers still allow the remaining four to run."""
    with patch("scrapers.myjobmag.scrape", return_value=[GOOD_JOB]), \
         patch("scrapers.jobwebkenya.scrape", return_value=[]), \
         patch("scrapers.brighter_monday.scrape", return_value=[]), \
         patch("scrapers.linkedin.scrape", side_effect=TimeoutError("blocked")), \
         patch("scrapers.jobrapido.scrape", side_effect=RuntimeError("403")), \
         patch("scrapers.alljobspo.scrape", return_value=[]), \
         patch("scrapers.cari.scrape", side_effect=ConnectionError("timeout")), \
         patch("main.sheets_client.save_jobs", return_value=(1, [GOOD_JOB])) as mock_save, \
         patch("main.whatsapp_notifier.send_jobs_to_whatsapp", return_value=1), \
         patch("main._append_activity_log"):
        main.run()

    mock_save.assert_called_once()


# ---------------------------------------------------------------------------
# Deduplication: same title+company from two sources → saved once
# ---------------------------------------------------------------------------

def test_cross_source_deduplication():
    """Same job title+company appearing on two boards should be deduplicated."""
    job_a = {**GOOD_JOB, "Source": "MyJobMag",    "Job URL": "https://myjobmag.co.ke/job/1"}
    job_b = {**GOOD_JOB, "Source": "JobWebKenya", "Job URL": "https://jobwebkenya.com/jobs/1"}

    with patch("scrapers.myjobmag.scrape", return_value=[job_a]), \
         patch("scrapers.jobwebkenya.scrape", return_value=[job_b]), \
         patch("scrapers.brighter_monday.scrape", return_value=[]), \
         patch("scrapers.linkedin.scrape", return_value=[]), \
         patch("scrapers.jobrapido.scrape", return_value=[]), \
         patch("scrapers.alljobspo.scrape", return_value=[]), \
         patch("scrapers.cari.scrape", return_value=[]), \
         patch("main.sheets_client.save_jobs", return_value=(1, [job_a])) as mock_save, \
         patch("main.whatsapp_notifier.send_jobs_to_whatsapp", return_value=1), \
         patch("main._append_activity_log"):
        main.run()

    saved_jobs = mock_save.call_args[0][0]
    assert len(saved_jobs) == 1  # deduplicated from 2 → 1


# ---------------------------------------------------------------------------
# No jobs found — nothing written, no crash
# ---------------------------------------------------------------------------

def test_no_jobs_found_does_not_write_to_sheet():
    """When all scrapers return empty lists, save_jobs must not be called."""
    with patch("scrapers.myjobmag.scrape", return_value=[]), \
         patch("scrapers.jobwebkenya.scrape", return_value=[]), \
         patch("scrapers.brighter_monday.scrape", return_value=[]), \
         patch("scrapers.linkedin.scrape", return_value=[]), \
         patch("scrapers.jobrapido.scrape", return_value=[]), \
         patch("scrapers.alljobspo.scrape", return_value=[]), \
         patch("scrapers.cari.scrape", return_value=[]), \
         patch("main.sheets_client.save_jobs") as mock_save, \
         patch("main.whatsapp_notifier.send_jobs_to_whatsapp"), \
         patch("main._append_activity_log"):
        main.run()

    mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# WhatsApp failure does not crash the pipeline
# ---------------------------------------------------------------------------

def test_whatsapp_failure_does_not_crash_pipeline():
    """If the WhatsApp notifier raises, the pipeline logs and continues."""
    with patch("scrapers.myjobmag.scrape", return_value=[GOOD_JOB]), \
         patch("scrapers.jobwebkenya.scrape", return_value=[]), \
         patch("scrapers.brighter_monday.scrape", return_value=[]), \
         patch("scrapers.linkedin.scrape", return_value=[]), \
         patch("scrapers.jobrapido.scrape", return_value=[]), \
         patch("scrapers.alljobspo.scrape", return_value=[]), \
         patch("scrapers.cari.scrape", return_value=[]), \
         patch("main.sheets_client.save_jobs", return_value=(1, [GOOD_JOB])), \
         patch("main.whatsapp_notifier.send_jobs_to_whatsapp",
               side_effect=RuntimeError("WhatsApp API is down")), \
         patch("main._append_activity_log"):
        main.run()  # must not raise
