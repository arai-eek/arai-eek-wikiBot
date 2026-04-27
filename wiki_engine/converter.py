"""
Conversion utilities for transforming Markdown to MediaWiki markup.
Uses the system's pandoc installation for high-quality conversion.
"""
import subprocess
import os

def md_to_wiki(md_content):
    """
    Convert Markdown string to MediaWiki markup string using Pandoc.
    """
    try:
        # We use pipe to pass the content to pandoc
        process = subprocess.Popen(
            ['pandoc', '-f', 'markdown', '-t', 'mediawiki'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=md_content)
        
        if process.returncode != 0:
            raise RuntimeError(f"Pandoc conversion failed: {stderr}")
            
        # Clean up local paths for the Wiki (e.g., ../media/image.png -> File:image.png)
        # Pandoc converts ![alt](../media/img.png) to [[File:../media/img.png|...]]
        wiki_content = stdout.replace("../media/", "")
        wiki_content = wiki_content.replace("media/", "")
        
        # Add default styling for the user (thumb|right)
        # We find [[File:filename.ext|...|caption]] and ensure it has thumb|right
        import re
        
        def clean_image_tag(match):
            filename = match.group(1)
            attrs = match.group(2).split('|')
            
            # Remove existing layout tags we want to override
            clean_attrs = [a for a in attrs if a not in ['thumb', 'right', 'left', 'center', 'none']]
            
            # Rebuild with our preferred style
            final_tag = f"[[File:{filename}|thumb|right|{'|'.join(clean_attrs)}]]"
            # Cleanup any double pipes that might have occurred
            return final_tag.replace('||', '|')

        wiki_content = re.sub(
            r'\[\[File:([^|\]]+)\|([^\]]+)\]\]',
            clean_image_tag,
            wiki_content
        )
        
        return wiki_content
    except FileNotFoundError:
        raise RuntimeError("Pandoc not found. Please install pandoc (e.g., sudo apt install pandoc).")

def convert_file(file_path):
    """
    Reads a markdown file and returns mediawiki markup.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    return md_to_wiki(md_content)

def wiki_to_md(wiki_content, site=None):
    """
    Convert MediaWiki markup string to Markdown string using Pandoc.
    If site is provided, it will replace image links with remote URLs.
    """
    try:
        process = subprocess.Popen(
            ['pandoc', '-f', 'mediawiki', '-t', 'gfm'], # GitHub Flavored Markdown
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=wiki_content)
        
        if process.returncode != 0:
            raise RuntimeError(f"Pandoc conversion failed: {stderr}")
            
        md_content = stdout
        
        # If site is provided, resolve image URLs
        if site:
            import re
            # Find all potential image references
            # 1. Markdown syntax: ![alt](filename)
            md_img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            # 2. HTML syntax: <img src="filename" ... />
            html_img_pattern = r'<img [^>]*src="([^"]+)"[^>]*>'
            # 3. Pandoc's weird gallery output: <File:filename>
            gallery_pattern = r'<File:([^>]+)>'
            
            # Collect all filenames
            filenames = []
            filenames += [m[1] for m in re.findall(md_img_pattern, md_content) if not m[1].startswith('http')]
            filenames += [m for m in re.findall(html_img_pattern, md_content) if not m.startswith('http')]
            filenames += [m for m in re.findall(gallery_pattern, md_content)]
            
            if filenames:
                from .images import get_image_urls
                url_map = get_image_urls(site, list(set(filenames)))
                
                # Replace Markdown images
                def replace_md(match):
                    alt, filename = match.group(1), match.group(2)
                    return f'![{alt}]({url_map.get(filename, filename)})'
                md_content = re.sub(md_img_pattern, replace_md, md_content)
                
                # Replace HTML images
                def replace_html(match):
                    src = match.group(1)
                    return match.group(0).replace(src, url_map.get(src, src))
                md_content = re.sub(html_img_pattern, replace_html, md_content)
                
                # Replace gallery items
                def replace_gallery(match):
                    filename = match.group(1)
                    url = url_map.get(filename, filename)
                    return f'![{filename}]({url})'
                md_content = re.sub(gallery_pattern, replace_gallery, md_content)

        return md_content
    except FileNotFoundError:
        raise RuntimeError("Pandoc not found. Please install pandoc.")
