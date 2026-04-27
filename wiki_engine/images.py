"""
Utilities for handling wiki images (uploads and downloads).
"""
import os
import time
import mwclient
from PIL import Image
from .config import WIKI_URL, WIKI_SCHEME, WIKI_PATH

def optimize_image(local_path, max_width=1024, quality=85):
    """
    Resizes and compresses an image locally before upload.
    """
    print(f"Optimizing '{local_path}' (max_width={max_width}, quality={quality})...")
    img = Image.open(local_path)
    
    # Resize if too wide
    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_height = int(float(img.height) * float(ratio))
        img = img.resize((max_width, new_height), Image.LANCZOS)
    
    # Save back to same path
    img.save(local_path, optimize=True, quality=quality)
    print(f"  New size: {os.path.getsize(local_path) / 1024:.1f} KB")
    return local_path

def upload_image(site, local_path, filename, summary, optimize=True, **kwargs):
    """
    Upload a local image to the wiki using system curl for maximum
    compatibility and to avoid Python-specific multipart issues.
    """
    import subprocess
    import json
    
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Local file not found: {local_path}")
        
    print(f"Uploading '{local_path}' as 'File:{filename}'...")
    
    try:
        if optimize:
            optimize_image(local_path)
            
        print(f"Uploading using mwclient with timeout...")
        
        with open(local_path, 'rb') as f:
            for attempt in range(3):
                try:
                    f.seek(0)
                    site.upload(f, filename, summary, ignore=True)
                    print(f"  Successfully uploaded 'File:{filename}'.")
                    return True
                except mwclient.errors.EditError as e:
                    if 'captcha' in str(e).lower():
                        print(f"  [CAPTCHA Required] for image upload.")
                        raise # For now, let it fail so we can solve it
                    else:
                        print(f"  Upload error (attempt {attempt+1}): {e}")
                        if attempt == 2: raise
                        time.sleep(2)
                except Exception as e:
                    # Catch timeout/connection errors specifically
                    print(f"  Connection issue during upload: {e}")
                    # Check if it succeeded anyway
                    time.sleep(5)
                    if site.pages[f"File:{filename}"].exists:
                        print(f"  ✅ Confirmed: File exists on wiki despite connection error.")
                        return True
                    if attempt == 2: raise
                    time.sleep(2)
            
    except Exception as e:
        print(f"  Upload failed: {e}")
        raise

def download_image(site, filename, local_path):
    """
    Download an image from the wiki.
    """
    if not filename.startswith("File:"):
        filename = "File:" + filename
        
    page = site.pages[filename]
    if not page.exists:
        raise FileNotFoundError(f"Wiki file not found: {filename}")
        
    print(f"Downloading '{filename}' to '{local_path}'...")
    with open(local_path, "wb") as f:
        page.download(f)
    print(f"  Successfully downloaded to '{local_path}'.")
    return local_path

def get_image_urls(site, filenames):
    """
    Fetch direct URLs for a list of wiki filenames in a batch.
    """
    if not filenames:
        return {}
    
    # Normalize names (add File: prefix if missing)
    full_names = []
    norm_to_orig = {}
    for f in filenames:
        # MediaWiki filenames are case-sensitive except for the first letter
        # and treat spaces/underscores as equivalent.
        full = f if f.startswith("File:") else f"File:{f}"
        full_names.append(full)
        
    # Batch query for imageinfo
    results = {}
    
    # MediaWiki limits batch size (usually 50)
    batch_size = 50
    for i in range(0, len(full_names), batch_size):
        batch = full_names[i:i + batch_size]
        res = site.api('query', titles='|'.join(batch), prop='imageinfo', iiprop='url')
        
        pages = res.get('query', {}).get('pages', {}).values()
        for page in pages:
            title = page.get('title', '')
            # Strip File: prefix
            api_name = title.replace("File:", "")
            ii = page.get('imageinfo', [])
            if ii:
                url = ii[0]['url']
                results[api_name] = url
                # Also add underscore version
                results[api_name.replace(" ", "_")] = url
                # Also add lowercase-first version if different
                if api_name and api_name[0].isupper():
                    lower_name = api_name[0].lower() + api_name[1:]
                    results[lower_name] = url
                    results[lower_name.replace(" ", "_")] = url
                
    return results
