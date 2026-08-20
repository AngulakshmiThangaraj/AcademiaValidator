import sys
import os

# Add root directory and backend directory to sys.path for Vercel Serverless Function entrypoint
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
backend_dir = os.path.join(root_dir, "backend")

for d in [root_dir, backend_dir]:
    if d not in sys.path:
        sys.path.insert(0, d)

# Import the FastAPI ASGI app instance
from backend.main import app
