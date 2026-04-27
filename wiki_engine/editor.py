"""
Helper functions for creating and editing wiki pages.
"""
import mwclient

def save_page(site, title, content, summary, create_only=False, **kwargs):
    """
    Save content to a wiki page with interactive CAPTCHA handling.
    """
    page = site.pages[title]
    
    if create_only and page.exists:
        print(f"Skipping '{title}': Page already exists.")
        return False
        
    try:
        if 'section' in kwargs:
            print(f"Saving section {kwargs['section']} to '{title}'...")
        else:
            print(f"Saving to '{title}'...")
        page.save(content, summary=summary, **kwargs)
        print(f"  Successfully saved '{title}'.")
        return True
    except mwclient.errors.EditError as e:
        # Check if this is a captcha challenge
        error_data = e.args[1]
        if 'captcha' in error_data:
            captcha = error_data['captcha']
            print(f"\n[CAPTCHA Required]")
            print(f"Question: {captcha.get('question', 'No question provided')}")
            
            # Prompt user for answer
            answer = input("Answer: ")
            
            # Retry with captcha details
            kwargs['captchaid'] = captcha.get('id')
            kwargs['captchaword'] = answer
            return save_page(site, title, content, summary, create_only, **kwargs)
        else:
            print(f"Error saving page: {e}")
            raise

def append_to_page(site, title, content, summary, newline=True, **kwargs):
    """
    Append content to the end of a wiki page.
    """
    page = site.pages[title]
    old_content = page.text() if page.exists else ""
    
    separator = "\n\n" if newline and old_content else ""
    new_content = old_content + separator + content
    
    # Use save_page to benefit from captcha handling
    return save_page(site, title, new_content, summary, **kwargs)
