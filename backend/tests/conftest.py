import sys
from pathlib import Path

# Ensure the src/ directory is on sys.path for imports during tests
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
