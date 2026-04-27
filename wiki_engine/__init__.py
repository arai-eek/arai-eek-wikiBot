"""
Hackteria Wiki Automation Toolkit - Engine Package.
"""
from .connection import connect
from .config import WIKI_URL, WIKI_USER
from .editor import save_page, append_to_page
from .images import upload_image, download_image
