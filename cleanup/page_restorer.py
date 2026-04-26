"""
Page Restorer — Recovery Tool

Fetches all pages deleted by Arai-eek-wikiBot and restores (undeletes) them.
This is a recovery tool to fix the false-positive deletions caused by the
flawed 'last editor' classification rule.

All deletions are restored unconditionally — true spam pages will be
re-identified and re-deleted in a subsequent pass using the correct rule
(original creator registered in Feb 2020).
"""
import time
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wiki_connection import connect
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

BOT_USERNAME = "Arai-eek-wikiBot"

def fetch_all_bot_deletions(site, console):
    """Fetch all pages deleted by the bot from the wiki deletion log."""
    console.print(f"\n[cyan]Fetching all deletions by {BOT_USERNAME}...[/cyan]")
    deleted_titles = []
    
    result = site.api('query', list='logevents', leuser=BOT_USERNAME,
                      letype='delete', lelimit=500)
    
    # Only care about 'delete' action, not 'restore'
    for entry in result['query']['logevents']:
        if entry.get('action') == 'delete':
            deleted_titles.append(entry['title'])
    
    while 'continue' in result:
        result = site.api('query', list='logevents', leuser=BOT_USERNAME,
                          letype='delete', lelimit=500, **result['continue'])
        for entry in result['query']['logevents']:
            if entry.get('action') == 'delete':
                deleted_titles.append(entry['title'])
    
    console.print(f"  Found [bold]{len(deleted_titles):,}[/bold] deleted pages to restore.")
    return deleted_titles


def restore_pages(site, titles, force=False):
    """Undelete a list of pages."""
    console = Console()
    total = len(titles)
    
    console.print(f"\n[bold cyan]♻️  Starting Page Restoration[/bold cyan]")
    console.print(f"Target: {total:,} pages\n")
    
    log_entries = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Restoring pages", total=total)
        
        for title in titles:
            reason = "Bot Recovery: Restoring false-positive deletion"
            success = False
            retries = 2
            
            while not success and retries >= 0:
                try:
                    site.api('undelete', title=title, reason=reason,
                             token=site.get_token('delete'))
                    status = "RESTORED"
                    success = True
                except Exception as e:
                    error_msg = str(e)
                    if 'badtoken' in error_msg or 'Invalid token' in error_msg:
                        site = connect(login=True)
                        retries -= 1
                        time.sleep(1)
                    elif 'cantundelete' in error_msg:
                        # Already exists (was never fully deleted, or already restored)
                        status = "SKIPPED (already exists)"
                        success = True
                    else:
                        console.print(f"[red]Error restoring {title}: {e}[/red]")
                        status = f"ERROR: {error_msg}"
                        success = True
            
            log_entries.append({
                "title": title,
                "status": status,
                "timestamp": datetime.now().isoformat()
            })
            
            progress.update(task, advance=1, description=f"{title[:50]}")
            time.sleep(0.5)  # gentle throttle
    
    return log_entries


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Restore pages deleted by the bot")
    parser.add_argument("--force", action="store_true", help="Skip confirmation")
    args = parser.parse_args()
    
    console = Console()
    site = connect(login=True)
    
    titles = fetch_all_bot_deletions(site, console)
    
    if not titles:
        console.print("[green]No bot deletions found. Nothing to restore.[/green]")
        sys.exit(0)
    
    if not args.force:
        from rich.prompt import Confirm
        if not Confirm.ask(f"Restore [bold]{len(titles):,}[/bold] pages?"):
            console.print("[yellow]Aborted.[/yellow]")
            sys.exit(0)
    
    log = restore_pages(site, titles)
    
    # Save log
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs("reports", exist_ok=True)
    log_path = f"reports/restore_log_{timestamp}.json"
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)
    
    restored = sum(1 for e in log if e['status'] == 'RESTORED')
    skipped = sum(1 for e in log if 'SKIPPED' in e['status'])
    errors = sum(1 for e in log if 'ERROR' in e['status'])
    
    console.print(f"\n[bold green]✅ Done![/bold green]")
    console.print(f"  Restored: {restored}")
    console.print(f"  Skipped:  {skipped}")
    console.print(f"  Errors:   {errors}")
    console.print(f"  Log: {log_path}")
