"""BL-195: exactly one email orchestrator, carrying the eval-time month raise and the timeout hints.

Static checks over the agent file. That it actually raises at eval time is shown by
`mix run --eval 'Code.eval_file(...)'` from the harness, which needs the sibling repo.
"""
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"
ORCHESTRATOR = AGENTS_DIR / "email_orchestrator.exs"


def test_exactly_one_email_orchestrator_exists():
    assert sorted(p.name for p in AGENTS_DIR.glob("*.exs")) == ["email_orchestrator.exs"]


def test_orchestrator_raises_at_eval_time_without_payslip_month():
    text = ORCHESTRATOR.read_text()
    assert 'month = System.get_env("PAYSLIP_MONTH") || raise "PAYSLIP_MONTH not set"' in text


def test_orchestrator_passes_month_explicitly_to_email_send():
    assert "Run: python3 email/scripts/email_send.py --month #{month}" in ORCHESTRATOR.read_text()


def test_orchestrator_carries_timeout_hints():
    text = ORCHESTRATOR.read_text()
    assert "timeout_ms: 120000" in text
    assert "timeout_ms: 300000" in text
