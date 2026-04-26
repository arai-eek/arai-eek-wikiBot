"""
Wiki connection utilities.
Handles authentication and provides a reusable site object.
"""
import mwclient
from config import (
    WIKI_URL, WIKI_PATH, WIKI_SCHEME,
    BOT_USERNAME, BOT_PASSWORD, MAX_LAG
)


def connect(login=True):
    """
    Connect to the Hackteria wiki and optionally log in.
    
    Returns:
        mwclient.Site: Connected (and authenticated) site object
    """
    print(f"Connecting to {WIKI_SCHEME}://{WIKI_URL}{WIKI_PATH} ...")
    
    site = mwclient.Site(
        WIKI_URL,
        path=WIKI_PATH,
        scheme=WIKI_SCHEME,
    )
    
    if login:
        if not BOT_USERNAME or not BOT_PASSWORD:
            raise ValueError(
                "BOT_USERNAME and BOT_PASSWORD must be set in .env file"
            )
        print(f"Logging in as {BOT_USERNAME} ...")
        site.login(BOT_USERNAME, BOT_PASSWORD)
        
        # Verify login and permissions via API
        result = site.api('query', meta='userinfo', uiprop='groups|rights')
        userinfo = result['query']['userinfo']
        print(f"  Logged in as: {userinfo['name']}")
        groups = userinfo.get('groups', [])
        rights = userinfo.get('rights', [])
        print(f"  Groups: {', '.join(groups)}")
        has_bot = 'bot' in groups
        has_delete = 'delete' in rights
        print(f"  Bot flag: {'✅' if has_bot else '❌'}")
        print(f"  Can delete: {'✅' if has_delete else '❌'}")
    else:
        print("  Connected (anonymous, read-only)")
    
    return site


def get_site_stats(site):
    """Get basic wiki statistics."""
    result = site.api('query', meta='siteinfo', siprop='statistics')
    return result['query']['statistics']


if __name__ == "__main__":
    # Quick connection test
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    console.print("\n[bold cyan]🕷️ Hackteria WikiBot — Connection Test[/bold cyan]\n")
    
    try:
        site = connect(login=True)
        stats = get_site_stats(site)
        
        table = Table(title="Wiki Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        table.add_row("Total pages", f"{stats['pages']:,}")
        table.add_row("Content articles", f"{stats['articles']:,}")
        table.add_row("Total edits", f"{stats['edits']:,}")
        table.add_row("Images", f"{stats['images']:,}")
        table.add_row("Users", f"{stats['users']:,}")
        table.add_row("Active users", f"{stats['activeusers']:,}")
        table.add_row("Admins", f"{stats['admins']:,}")
        
        console.print(table)
        console.print("\n[bold green]✅ Connection successful![/bold green]\n")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Connection failed: {e}[/bold red]\n")
        raise
