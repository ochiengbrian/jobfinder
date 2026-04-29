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

def test_mombasa_includes_kenya_nationwide(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Kenya") is True

def test_mombasa_includes_remote(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Remote") is True

def test_mombasa_includes_anywhere(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Mombasa")
    assert config.matches_location("Anywhere") is True

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

def test_nairobi_target_includes_kenya_nationwide(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Nairobi")
    assert config.matches_location("Kenya") is True

def test_nairobi_target_excludes_mombasa(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Nairobi")
    assert config.matches_location("Mombasa") is False

def test_nairobi_target_excludes_kisumu(monkeypatch):
    monkeypatch.setattr(config, "JOB_LOCATION", "Nairobi")
    assert config.matches_location("Kisumu") is False
