"""
Utilities for managing local wiki drafts.
"""
import os

DRAFTS_DIR = os.path.join(os.path.dirname(__file__), "..", "drafts")
os.makedirs(DRAFTS_DIR, exist_ok=True)

def write_draft(name, content):
    """Save content to a local draft file (.md or .wiki)."""
    if not name.endswith(".wiki") and not name.endswith(".md"):
        name += ".md"  # Default to Markdown now
    
    path = os.path.join(DRAFTS_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Draft saved to: {path}")
    return path

def read_draft(name):
    """Read content from a local draft file."""
    # If no extension, try .md then .wiki
    exts = ["", ".md", ".wiki"]
    path = None
    
    for ext in exts:
        test_path = os.path.join(DRAFTS_DIR, name + ext)
        if os.path.exists(test_path):
            path = test_path
            break
        # Also check if 'name' already contains the path
        if os.path.exists(name):
            path = name
            break
    
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"Draft not found: {name}")
        
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def list_drafts():
    """List all available .wiki files in the drafts directory."""
    files = [f for f in os.listdir(DRAFTS_DIR) if f.endswith(".wiki")]
    return sorted(files)
