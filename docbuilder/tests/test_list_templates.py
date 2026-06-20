import json
import subprocess
import sys
from pathlib import Path

import pytest

import list_templates
from list_templates import load_catalogue, resolve_catalogue

USE_CASE_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = USE_CASE_ROOT / "data" / "templates"


# --- unit (load_catalogue) ---

def test_demo_catalogue_loads():
    cat = load_catalogue(TEMPLATES_DIR, "demo")
    assert cat["tenant_id"] == "demo"
    assert [d["doc_type"] for d in cat["doc_types"]] == ["proposal"]


def test_demo_catalogue_variant_fields():
    cat = load_catalogue(TEMPLATES_DIR, "demo")
    variant = cat["doc_types"][0]["variants"][0]
    assert variant["version"] == "v1"
    assert variant["label"] == "Standard"
    assert variant["output_formats"] == ["xlsx", "docx", "pdf"]
    assert variant["has_base_files"] == {"xlsx": True, "docx": True}
    assert variant["has_narrative"] is True


def test_unknown_tenant_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_catalogue(str(tmp_path), "nope")


def test_missing_catalogue_raises(tmp_path):
    # tenant directory exists but has no catalogue.json
    (tmp_path / "acme").mkdir()
    with pytest.raises(FileNotFoundError):
        load_catalogue(str(tmp_path), "acme")


# --- CLI ---

def test_cli_demo_tenant():
    result = subprocess.run(
        [sys.executable, "scripts/list_templates.py", "--tenant", "demo"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 0, result.stderr
    cat = json.loads(result.stdout)  # output is valid JSON
    assert cat["tenant_id"] == "demo"
    assert len(cat["doc_types"]) >= 1


def test_cli_unknown_tenant_exits_1():
    result = subprocess.run(
        [sys.executable, "scripts/list_templates.py", "--tenant", "ghost"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 1
    assert "error" in result.stderr


def test_cli_custom_templates_dir(tmp_path):
    tenant_dir = tmp_path / "acme"
    tenant_dir.mkdir()
    (tenant_dir / "catalogue.json").write_text(
        json.dumps({"tenant_id": "acme", "doc_types": []})
    )
    result = subprocess.run(
        [sys.executable, "scripts/list_templates.py",
         "--tenant", "acme", "--templates-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["tenant_id"] == "acme"


# --- Drive routing (m2b) ---

def test_resolve_catalogue_flat_when_no_drive_id():
    # No drive_id → flat local file (m2a behaviour preserved).
    cat = resolve_catalogue("demo", TEMPLATES_DIR, None)
    assert cat["tenant_id"] == "demo"


def test_resolve_catalogue_uses_drive_when_id_set(monkeypatch):
    # drive_id present → the Drive loader is used (mocked; no creds needed).
    calls = {}

    def fake_drive(tenant_id, drive_id):
        calls["args"] = (tenant_id, drive_id)
        return {"tenant_id": tenant_id, "doc_types": [], "_source": "drive"}

    monkeypatch.setattr(list_templates, "load_catalogue_drive", fake_drive)
    cat = resolve_catalogue("demo", TEMPLATES_DIR, "DRIVE_ROOT_123")
    assert cat["_source"] == "drive"
    assert calls["args"] == ("demo", "DRIVE_ROOT_123")
