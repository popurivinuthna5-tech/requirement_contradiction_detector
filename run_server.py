import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

import uvicorn
from app.config import HOST, PORT

if __name__ == "__main__":
    print(f"Starting Requirement Conflict & Overlap Analyzer server on http://{HOST}:{PORT} ...")
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)
