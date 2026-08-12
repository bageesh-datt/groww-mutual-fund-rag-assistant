"""
Vercel Serverless Function Entrypoint
Exposes the FastAPI application from backend.app.main
"""

import sys
from pathlib import Path

# Add project root and backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"

if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.app.main import app
