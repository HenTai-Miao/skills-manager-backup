"""
Make `scripts/token_estimator.py` importable as `token_estimator` so tests
can import the library functions without shelling out to the CLI.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
