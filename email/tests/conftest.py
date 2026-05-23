"""Test configuration for email unit tests."""
import sys
from pathlib import Path

# Add email/scripts/ so tests can import email_download_template directly,
# avoiding the stdlib email package name collision.
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
