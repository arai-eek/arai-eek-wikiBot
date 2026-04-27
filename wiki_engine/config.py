"""
Configuration for the Hackteria Wiki Automation Toolkit.
"""
import os
from dotenv import load_dotenv

# Search for .env in the parent directory (root)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Wiki connection
WIKI_URL = os.getenv("WIKI_URL", "hackteria.org")
WIKI_PATH = os.getenv("WIKI_PATH", "/wiki/")
WIKI_USER = os.getenv("WIKI_USER") or os.getenv("BOT_USERNAME")
WIKI_PASS = os.getenv("WIKI_PASS") or os.getenv("BOT_PASSWORD")

# Use HTTPS
WIKI_SCHEME = "https"

# Rate limiting
MAX_LAG = 5
EDIT_THROTTLE = 2
REQUEST_THROTTLE = 0.5

# Output
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
