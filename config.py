"""
Configuration for the Hackteria WikiBot.
Loads credentials from .env file and provides wiki connection settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Wiki connection
WIKI_URL = os.getenv("WIKI_URL", "hackteria.org")
WIKI_PATH = os.getenv("WIKI_PATH", "/wiki/")
WIKI_USER = os.getenv("WIKI_USER")
WIKI_PASS = os.getenv("WIKI_PASS")

# Use HTTPS
WIKI_SCHEME = "https"

# Rate limiting - respect the server
MAX_LAG = 5          # seconds; bot waits if server lag exceeds this
EDIT_THROTTLE = 2    # seconds between edits
REQUEST_THROTTLE = 0.5  # seconds between API requests

# Output (for logs/reports)
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
