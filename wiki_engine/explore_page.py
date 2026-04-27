import os
import sys
from wiki_engine import connect

def explore_page(title):
    site = connect(login=False) # No need to login for reading
    page = site.pages[title]
    
    if not page.exists:
        print(f"Page '{title}' does not exist.")
        return

    print(f"\n--- Page: {title} ---")
    print(f"ID: {page.pageid}")
    
    # Get sections
    print("\nSections:")
    result = site.api('parse', page=title, prop='sections')
    sections = result.get('parse', {}).get('sections', [])
    
    for s in sections:
        print(f"  {s['number']}. {s['line']} (index: {s['index']}, level: {s['level']})")

    # Get full text
    # text = page.text()
    # print(f"\nFull Text Length: {len(text)} characters")

if __name__ == "__main__":
    title = sys.argv[1] if len(sys.argv) > 1 else "OpenScienceLab"
    explore_page(title)
