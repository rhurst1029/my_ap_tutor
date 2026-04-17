"""
Pytest configuration for MyAPTutor backend tests.
Sets sys.path so backend modules resolve, provides shared fixtures.
NEVER writes to data/students/ in tests.
"""
import sys, os
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# Dummy key so config.py doesn't fail on import
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-real")

from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def tmp_student_dir(tmp_path: Path) -> Path:
    """Temporary directory mimicking data/students/{name}_data/. Use instead of real dir."""
    d = tmp_path / "test_student_data"
    d.mkdir()
    return d
