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
