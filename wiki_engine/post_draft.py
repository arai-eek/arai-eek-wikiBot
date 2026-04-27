"""
Script to upload a local draft to the wiki.
"""
import sys
import os
from .connection import connect
from .editor import save_page
from .drafter import read_draft
from .converter import md_to_wiki

import argparse

def main():
    parser = argparse.ArgumentParser(description="Upload a local draft to the wiki.")
    parser.add_argument("draft", help="Name of the draft file (in drafts/ folder)")
    parser.add_argument("title", help="Title of the wiki page")
    parser.add_argument("--section", type=int, help="Optional section index to update")
    parser.add_argument("--summary", help="Optional edit summary")
    
    args = parser.parse_args()

    try:
        # 1. Read the local content
        content = read_draft(args.draft)
        
        # 2. Convert if it's markdown
        if args.draft.endswith(".md"):
            print(f"Converting Markdown draft '{args.draft}' to MediaWiki format...")
            content = md_to_wiki(content)
            print(f"  Conversion complete ({len(content)} characters).")
            
            # Save a local .wiki file for verification
            wiki_preview_path = os.path.join(os.path.dirname(__file__), "..", "drafts", args.draft.replace(".md", ".wiki"))
            with open(wiki_preview_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  Local wiki preview saved to: {wiki_preview_path}")
        else:
            print(f"Read draft '{args.draft}' ({len(content)} characters).")

        # 3. Connect to the wiki
        site = connect(login=True)

        # 4. Save to the wiki
        summary = args.summary or f"Uploading local draft: {os.path.basename(args.draft)}"
        kwargs = {}
        if args.section is not None:
            kwargs['section'] = args.section
            
        save_page(site, args.title, content, summary, **kwargs)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to post draft: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
