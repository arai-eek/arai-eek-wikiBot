"""
Simple example script for interacting with the Hackteria Wiki.
Shows how to read, edit, and list pages.
"""
from wiki_connection import connect

def run_example():
    # 1. Connect and login
    site = connect(login=True)

    # 2. Read a page
    target_page_name = "Main Page"
    page = site.pages[target_page_name]
    
    print(f"\n--- Reading: {target_page_name} ---")
    if page.exists:
        # Get the text content
        text = page.text()
        print(f"Page length: {len(text)} characters")
        print(f"First 100 chars: {text[:100]}...")
    else:
        print("Page does not exist.")

    # 3. List pages in a category
    category_name = "Projects"
    print(f"\n--- Listing Category: {category_name} ---")
    category = site.categories[category_name]
    for i, p in enumerate(category.members()):
        print(f"  {i+1}. {p.name}")
        if i >= 4: # limit to 5 for example
            print("  ...")
            break

    # 4. Edit a page (sandbox/test page)
    # BE CAREFUL: This will actually change the wiki!
    test_page_name = "User:Arai-eek-wikiBot/Sandbox"
    print(f"\n--- Editing: {test_page_name} ---")
    test_page = site.pages[test_page_name]
    
    # Read existing content
    current_content = test_page.text() if test_page.exists else ""
    
    # Append a small timestamp or comment
    import datetime
    new_comment = f"\n* Bot test at {datetime.datetime.now().isoformat()}"
    
    # Save the page (uncomment the line below to actually save)
    # test_page.save(current_content + new_comment, summary="Testing WikiBot example script")
    print("  [Note] Save line is commented out in example.py for safety.")

if __name__ == "__main__":
    run_example()
