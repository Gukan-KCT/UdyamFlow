"""
Vercel Serverless Function – catch-all handler for the FastAPI backend.
Works when Vercel project Root Directory is set to repo root (./).
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Ensure the backend package root is on sys.path
# ---------------------------------------------------------------------------
_current = Path(__file__).resolve().parent
_candidates = [
    _current.parent / "FilePulse" / "src" / "backend",
    _current.parent / "src" / "backend",
]
for _candidate in _candidates:
    if (_candidate / "main.py").exists():
        _backend_dir = str(_candidate)
        if _backend_dir not in sys.path:
            sys.path.insert(0, _backend_dir)
        break

# ---------------------------------------------------------------------------
# 2. Set VERCEL env-flag
# ---------------------------------------------------------------------------
os.environ.setdefault("VERCEL", "1")

# ---------------------------------------------------------------------------
# 3. Import the FastAPI app – Vercel's ASGI adapter picks this up
# ---------------------------------------------------------------------------
from main import app  # noqa: E402
