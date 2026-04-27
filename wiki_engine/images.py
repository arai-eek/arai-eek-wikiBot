"""
Utilities for handling wiki images (uploads and downloads).
"""
import os
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
            
        print(f"Uploading using system curl for maximum compatibility...")
        
        # Get authentication details from the mwclient session
        token = site.get_token('csrf')
        cookie_string = "; ".join([f"{k}={v}" for k, v in site.connection.cookies.items()])
        api_url = f"{WIKI_SCHEME}://{WIKI_URL}{WIKI_PATH}api.php"
        
        cmd = [
            'curl', '-X', 'POST', api_url,
            '-H', f'Cookie: {cookie_string}',
            '-F', 'action=upload',
            '-F', f'filename={filename}',
            '-F', f'token={token}',
            '-F', f'file=@{local_path}',
            '-F', 'ignorewarnings=1',
            '-F', 'format=json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            res = json.loads(result.stdout)
            if res.get('upload', {}).get('result') == 'Success':
                print(f"  Successfully uploaded 'File:{filename}'.")
                return True
            else:
                print(f"  Upload response: {res}")
                return False
        else:
            print(f"  Curl failed: {result.stderr}")
            return False
            
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
