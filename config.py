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
BOT_USERNAME = os.getenv("BOT_USERNAME")
BOT_PASSWORD = os.getenv("BOT_PASSWORD")

# Use HTTPS
WIKI_SCHEME = "https"

# Rate limiting - respect the server
MAX_LAG = 5          # seconds; bot waits if server lag exceeds this
EDIT_THROTTLE = 2    # seconds between edits
REQUEST_THROTTLE = 0.5  # seconds between API requests

# Output
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Spam detection heuristics
SPAM_TITLE_PATTERNS = [
    r"\d+ (?:Ways|Methods|Tips|Easy|Smart|Best|Top|Simple)",
    r"(?:Buy|Cheap|Online|Pharmacy|Casino|Poker|Betting|Gambling)",
    r"(?:Viagra|Cialis|Weight Loss|Diet|Supplement)",
    r"(?:SEO|Marketing|Backlink|Traffic|Cryptocurrency|Bitcoin|Forex)",
    r"Hướng Dẫn",  # Vietnamese SEO spam pattern seen in allpages
    r"(?:Home Remedies|Dangerous Chemicals|Food Waste|Spring Clean)",
    r"(?:Gold Medal|Year In Music)",  # generic non-wiki content
]

# Known legitimate page prefixes/patterns  
LEGIT_PREFIXES = [
    "HackteriaLab",
    "Hackteria",
    "Generic Lab",
    "DIY",
    "DIWO",
    "Workshop",
    "OpenScienceLab",
    "CoLabs",
    "GlobalLAMP",
    "HUMUS",
    "BadLab",
    "MedTech",
    "Temporary Lab",
    "BioElectronics",
    "Biohacking",
]
