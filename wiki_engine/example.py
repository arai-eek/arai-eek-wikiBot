"""
Simple example script for interacting with the Hackteria Wiki.
"""
from .connection import connect

def run_example():
    # 1. Connect and login
    site = connect(login=True)

    # 2. Read a page
    page_name = "Main Page"
    page = site.pages[page_name]
    print(f"\n--- Reading: {page.name} ---")
    if page.exists:
        print(f"Page length: {len(page.text())} characters")
    else:
        print(f"Page '{page_name}' does not exist.")

    # 3. List some category members
    cat_name = "Workshop"
    print(f"\n--- Listing Category: {cat_name} ---")
    for i, p in enumerate(site.categories[cat_name].members()):
        print(f"  {i+1}. {p.name}")
        if i >= 4: break

if __name__ == "__main__":
    run_example()
