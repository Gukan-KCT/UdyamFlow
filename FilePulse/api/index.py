"""
Vercel Serverless Function – catch-all handler for the FastAPI backend.

Vercel invokes this module for every ``/api/*`` request.  We add
``src/backend`` to ``sys.path`` so all the existing ``app.*`` and ``config``
imports work unchanged.

Vercel's @vercel/python runtime natively supports ASGI applications.
It detects the ``app`` variable and serves it directly – no Mangum needed.
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Ensure the backend package root is on ``sys.path``
# ---------------------------------------------------------------------------
_BACKEND_DIR = str(Path(__file__).resolve().parent.parent / "src" / "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# ---------------------------------------------------------------------------
# 2. Set VERCEL env-flag (Vercel also sets it, but belt-and-suspenders)
# ---------------------------------------------------------------------------
os.environ.setdefault("VERCEL", "1")

# ---------------------------------------------------------------------------
# 3. Import the FastAPI ``app`` – Vercel's ASGI adapter picks this up
# ---------------------------------------------------------------------------
from main import app  # noqa: E402  – path must be set first

# Vercel's @vercel/python runtime detects the ``app`` ASGI application
# and handles it automatically.  No additional adapter is needed.
