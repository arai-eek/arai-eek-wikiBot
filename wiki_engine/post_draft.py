"""
Script to upload a local draft to the wiki.
"""
import sys
import os
from .connection import connect
from .editor import save_page
from .drafter import read_draft
from .converter import md_to_wiki

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 -m wiki_engine.post_draft <draft_name> <wiki_page_title>")
        print("Example: python3 -m wiki_engine.post_draft page.md 'User:MyUser/Sandbox'")
        sys.exit(1)

    draft_name = sys.argv[1]
    page_title = sys.argv[2]

    try:
        # 1. Read the local content
        content = read_draft(draft_name)
        
        # 2. Convert if it's markdown
        if draft_name.endswith(".md"):
            print(f"Converting Markdown draft '{draft_name}' to MediaWiki format...")
            content = md_to_wiki(content)
            print(f"  Conversion complete ({len(content)} characters).")
            
            # Save a local .wiki file for verification
            wiki_preview_path = os.path.join(os.path.dirname(__file__), "..", "drafts", draft_name.replace(".md", ".wiki"))
            with open(wiki_preview_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  Local wiki preview saved to: {wiki_preview_path}")
        else:
            print(f"Read draft '{draft_name}' ({len(content)} characters).")

        # 3. Connect to the wiki
        site = connect(login=True)

        # 3. Save to the wiki
        summary = f"Uploading local draft: {os.path.basename(draft_name)}"
        save_page(site, page_title, content, summary)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to post draft: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
