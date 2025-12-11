import pytest
import sys
from pathlib import Path
import tempfile
import os

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Create a mock frontend directory before any imports
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(tmp_path_factory):
    """Set up test environment before tests run"""
    # Create a temporary frontend directory
    frontend_dir = Path(__file__).parent.parent / "frontend"
    if not frontend_dir.exists():
        frontend_dir.mkdir(parents=True)
        (frontend_dir / "index.html").write_text("<html><body>Test</body></html>")
        yield
        # Cleanup
        if frontend_dir.exists():
            import shutil
            shutil.rmtree(frontend_dir)
    else:
        yield
