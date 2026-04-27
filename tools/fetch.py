import sys
import argparse
from wiki_engine import connect
from wiki_engine.drafter import fetch_to_draft

def main():
    parser = argparse.ArgumentParser(description="Fetch a wiki page into a local draft.")
    parser.add_argument("title", help="Title of the wiki page")
    parser.add_argument("--section", type=int, help="Optional section index to fetch")
    parser.add_argument("--raw", action="store_true", help="Fetch as raw .wiki instead of .md")
    
    args = parser.parse_args()
    
    site = connect(login=False)
    try:
        path = fetch_to_draft(site, args.title, section=args.section, as_md=not args.raw)
        print(f"\n✅ Fetched '{args.title}' to {path}")
        print(f"You can now edit this file locally.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
