"""
Tests for config.matches_location() — the location filter used by all scrapers.
Uses monkeypatch to test multiple JOB_LOCATION values without touching .env.
"""
import pytest
import config


# ---------------------------------------------------------------------------
# Empty / unspecified locations are always included
# ---------------------------------------------------------------------------

def test_empty_string_always_matches():
    assert config.matches_location("") is True

def test_whitespace_always_matches():
    assert config.matches_location("   ") is True


# ---------------------------------------------------------------------------
# JOB_LOCATION = "Mombasa" (default)
# ---------------------------------------------------------------------------

def test_mombasa_matches_exactly(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Mombasa") is True

def test_mombasa_matches_with_suburb(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Mombasa CBD") is True

def test_mombasa_matches_case_insensitive(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("MOMBASA") is True

def test_mombasa_matches_coast_county_kilifi(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Kilifi") is True

def test_mombasa_matches_coast_county_kwale(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Kwale") is True

def test_mombasa_matches_coast_county_malindi(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Malindi") is True

def test_mombasa_matches_coast_keyword(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Coast Province") is True

def test_mombasa_excludes_kenya_tagged_jobs(monkeypatch):
    """Jobs tagged 'Kenya' are Nairobi-based national listings, not Mombasa jobs."""
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Kenya") is False

def test_mombasa_includes_remote(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Remote") is True

def test_mombasa_includes_hybrid(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Hybrid") is True

def test_mombasa_includes_wfh(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Work from home") is True

def test_mombasa_excludes_nairobi(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Nairobi") is False

def test_mombasa_excludes_kisumu(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Kisumu") is False

def test_mombasa_excludes_nakuru(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Nakuru") is False

def test_mombasa_excludes_foreign_city(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Lagos, Nigeria") is False


# ---------------------------------------------------------------------------
# JOB_LOCATION = "Kenya" — include everything
# ---------------------------------------------------------------------------

def test_kenya_target_includes_nairobi(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Kenya")
    assert config.matches_location("Nairobi") is True

def test_kenya_target_includes_mombasa(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Kenya")
    assert config.matches_location("Mombasa") is True

def test_kenya_target_includes_kisumu(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Kenya")
    assert config.matches_location("Kisumu") is True

def test_kenya_target_includes_foreign(monkeypatch):
    """When JOB_LOCATION=Kenya we do not filter by location at all."""
    monkeypatch.setattr(config, "JOB_LOCATION", "Kenya")
    assert config.matches_location("Lagos, Nigeria") is True


# ---------------------------------------------------------------------------
# JOB_LOCATION = "Nairobi" — different city, not Mombasa
# ---------------------------------------------------------------------------

def test_nairobi_target_matches_nairobi(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Nairobi")
    assert config.matches_location("Nairobi") is True

def test_nairobi_target_excludes_kenya_tagged(monkeypatch):
    """Kenya-tagged jobs are excluded for any specific city target."""
    monkeypatch.setattr(config, "JOB_LOCATION", "Nairobi")
    assert config.matches_location("Kenya") is False

def test_nairobi_target_excludes_mombasa(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Nairobi")
    assert config.matches_location("Mombasa") is False

def test_nairobi_target_excludes_kisumu(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Nairobi")
    assert config.matches_location("Kisumu") is False

def test_nairobi_target_excludes_kenya_tagged(monkeypatch):
    """Kenya-tagged jobs are excluded even for Nairobi target — set JOB_LOCATION=Kenya to include."""
    monkeypatch.setattr(config, "JOB_LOCATION", "Nairobi")
    assert config.matches_location("Kenya") is False


# ---------------------------------------------------------------------------
# is_tech_job — title relevance filter
# ---------------------------------------------------------------------------

def test_is_tech_job_software_engineer():
    assert config.is_tech_job("Software Engineer") is True

def test_is_tech_job_frontend_engineer():
    assert config.is_tech_job("Senior Frontend Engineer") is True

def test_is_tech_job_backend_developer():
    assert config.is_tech_job("Backend Developer") is True

def test_is_tech_job_data_analyst():
    assert config.is_tech_job("Data Analyst") is True

def test_is_tech_job_data_scientist():
    assert config.is_tech_job("Data Scientist") is True

def test_is_tech_job_network_engineer():
    assert config.is_tech_job("Network Engineer") is True

def test_is_tech_job_it_officer():
    assert config.is_tech_job("IT Officer") is True

def test_is_tech_job_information_systems():
    assert config.is_tech_job("Information Systems Officer") is True

def test_is_tech_job_devops():
    assert config.is_tech_job("DevOps Engineer") is True

def test_is_tech_job_cybersecurity():
    assert config.is_tech_job("Cybersecurity Analyst") is True

def test_is_tech_job_rejects_compliance_officer():
    assert config.is_tech_job("Compliance Officer") is False

def test_is_tech_job_rejects_accounts_intern():
    assert config.is_tech_job("Accounts Intern") is False

def test_is_tech_job_rejects_marketing_executive():
    assert config.is_tech_job("Marketing Executive") is False

def test_is_tech_job_rejects_claims_officer():
    assert config.is_tech_job("Claims Officer") is False

def test_is_tech_job_rejects_country_director():
    assert config.is_tech_job("Country Director") is False

def test_is_tech_job_rejects_elevator_mechanic():
    assert config.is_tech_job("Elevator Mechanic") is False

def test_is_tech_job_rejects_procurement_assistant():
    assert config.is_tech_job("Procurement Assistant") is False

def test_is_tech_job_rejects_submit_cvs():
    assert config.is_tech_job("Submit CVs – New Recruitment") is False
