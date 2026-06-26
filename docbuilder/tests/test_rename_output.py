import json
import subprocess
import sys
from pathlib import Path

import pytest

from rename_output import doc_type_base, rename_outputs, safe_segment, slugify

USE_CASE_ROOT = Path(__file__).parent.parent


# --- unit: helpers ---

def test_slugify_basic():
    assert slugify("Acme Corp") == "acme_corp"


def test_slugify_strips_punctuation():
    assert slugify("Acme Corp, Inc.") == "acme_corp_inc"
    assert slugify("Béta-Co!") == "bta-co"  # non-ascii (é) + "!" stripped, hyphen kept


def test_doc_type_base_strips_version():
    assert doc_type_base("proposal_v1") == "proposal"
    assert doc_type_base("master_service_agreement_v2") == "master_service_agreement"


def test_doc_type_base_no_version_unchanged():
    assert doc_type_base("invoice") == "invoice"


def test_safe_segment_iso_unchanged():
    assert safe_segment("2026-06-20") == "2026-06-20"


def test_safe_segment_display_date_spaces():
    assert safe_segment("20 Jun 2026") == "20_Jun_2026"


# --- unit: rename_outputs ---

def _make(out, name):
    (out / name).write_text("x")


# --- candidate_name fallback (m6 t4b) ---

def test_rename_uses_candidate_name_for_offer_letter(tmp_path):
    # Offer-letter context has candidate_name (no client_name) → slug from candidate_name.
    _make(tmp_path, "offer_letter_v1.docx")
    pairs = rename_outputs(
        str(tmp_path), "offer_letter_v1",
        {"candidate_name": "Ajay Rao", "date": "2026-07-01", "doc_type": "offer_letter"},
    )
    assert Path(pairs[0]["renamed"]).name == "ajay_rao_offer_letter_2026-07-01.docx"
    assert (tmp_path / "ajay_rao_offer_letter_2026-07-01.docx").exists()


def test_rename_client_name_takes_precedence(tmp_path):
    # When both present, client_name wins (invoices/proposals unchanged).
    _make(tmp_path, "invoice_v1.pdf")
    pairs = rename_outputs(
        str(tmp_path), "invoice_v1",
        {"client_name": "Acme Corp", "candidate_name": "Ignored", "date": "2026-06-20"},
    )
    assert Path(pairs[0]["renamed"]).name.startswith("acme_corp_")


def test_rename_raises_when_neither_name(tmp_path):
    _make(tmp_path, "x_v1.pdf")
    with pytest.raises(ValueError, match="client_name.*candidate_name"):
        rename_outputs(str(tmp_path), "x_v1", {"date": "2026-06-20"})


def test_rename_produces_expected_filenames(tmp_path):
    for ext in ("xlsx", "docx", "pdf"):
        _make(tmp_path, f"proposal_v1.{ext}")
    pairs = rename_outputs(
        str(tmp_path), "proposal_v1",
        {"client_name": "Acme Corp", "date": "2026-06-20", "doc_type": "proposal"},
    )
    renamed = sorted(Path(p["renamed"]).name for p in pairs)
    assert renamed == [
        "acme_corp_proposal_2026-06-20.docx",
        "acme_corp_proposal_2026-06-20.pdf",
        "acme_corp_proposal_2026-06-20.xlsx",
    ]
    # originals are gone, renamed exist
    assert not (tmp_path / "proposal_v1.xlsx").exists()
    assert (tmp_path / "acme_corp_proposal_2026-06-20.xlsx").exists()


def test_doc_type_fallback_to_prefix_base(tmp_path):
    _make(tmp_path, "proposal_v1.pdf")
    pairs = rename_outputs(
        str(tmp_path), "proposal_v1",
        {"client_name": "Acme Corp", "date": "2026-06-20"},  # no doc_type
    )
    assert Path(pairs[0]["renamed"]).name == "acme_corp_proposal_2026-06-20.pdf"


def test_non_matching_files_untouched(tmp_path):
    _make(tmp_path, "proposal_v1.pdf")
    _make(tmp_path, "pipeline_spec.json")        # intermediate — must not be renamed
    _make(tmp_path, "pipeline_raw_main.json")
    pairs = rename_outputs(
        str(tmp_path), "proposal_v1",
        {"client_name": "Acme", "date": "2026-06-20"},
    )
    assert len(pairs) == 1
    assert (tmp_path / "pipeline_spec.json").exists()
    assert (tmp_path / "pipeline_raw_main.json").exists()


def test_missing_client_name_raises(tmp_path):
    with pytest.raises(ValueError, match="client_name"):
        rename_outputs(str(tmp_path), "proposal_v1", {"date": "2026-06-20"})


def test_missing_date_raises(tmp_path):
    with pytest.raises(ValueError, match="date"):
        rename_outputs(str(tmp_path), "proposal_v1", {"client_name": "Acme"})


def test_no_matches_returns_empty(tmp_path):
    pairs = rename_outputs(
        str(tmp_path), "proposal_v1",
        {"client_name": "Acme", "date": "2026-06-20"},
    )
    assert pairs == []


# --- CLI ---

def test_cli_renames_and_prints_pairs(tmp_path):
    (tmp_path / "proposal_v1.pdf").write_text("x")
    result = subprocess.run(
        [sys.executable, "scripts/rename_output.py",
         "--output-dir", str(tmp_path), "--filename-prefix", "proposal_v1",
         "--context", '{"client_name":"Acme Corp","date":"2026-06-20","doc_type":"proposal"}'],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 0, result.stderr
    pairs = json.loads(result.stdout)
    assert Path(pairs[0]["renamed"]).name == "acme_corp_proposal_2026-06-20.pdf"


def test_cli_missing_field_exits_1(tmp_path):
    result = subprocess.run(
        [sys.executable, "scripts/rename_output.py",
         "--output-dir", str(tmp_path), "--filename-prefix", "proposal_v1",
         "--context", '{"client_name":"Acme"}'],  # no date
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 1
    assert "date" in result.stderr


def test_cli_output_flag_writes_file(tmp_path):
    (tmp_path / "proposal_v1.pdf").write_text("x")
    out_file = tmp_path / "renamed.json"
    result = subprocess.run(
        [sys.executable, "scripts/rename_output.py",
         "--output-dir", str(tmp_path), "--filename-prefix", "proposal_v1",
         "--context", '{"client_name":"Acme","date":"2026-06-20"}',
         "--output", str(out_file)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(out_file)
    pairs = json.loads(out_file.read_text())
    assert Path(pairs[0]["renamed"]).name == "acme_proposal_2026-06-20.pdf"
