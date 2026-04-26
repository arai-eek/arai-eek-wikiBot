"""
Spam Remover — Phase 2 Cleanup Tool

Loads a spam audit JSON report and deletes pages classified as SPAM.
Requires admin/sysop rights (which our bot account has).

Features:
  - Dry-run mode by default
  - Logging of all deletions
  - Batching and rate limiting
  - Optional limit on number of deletions
"""
import json
import time
import os
import sys
from datetime import datetime

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wiki_connection import connect
from config import EDIT_THROTTLE, MAX_LAG

from rich.console import Console
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

def load_audit_report(file_path):
    """Load the audit results from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def delete_spam_pages(site, pages_to_delete, dry_run=True, limit=None, force=False):
    """
    Delete a list of spam pages from the wiki.
    """
    console = Console()
    
    if limit:
        pages_to_delete = pages_to_delete[:limit]
    
    total = len(pages_to_delete)
    mode_str = "[bold yellow]DRY-RUN[/bold yellow]" if dry_run else "[bold red]DELETE[/bold red]"
    
    console.print(f"\n[bold cyan]🧹 Starting Spam Removal ({mode_str} mode)[/bold cyan]")
    console.print(f"Target: {total:,} pages\n")
    
    if not dry_run and not force:
        if not Confirm.ask(f"[bold red]CRITICAL:[/bold red] You are about to DELETE {total:,} pages. Proceed?"):
            console.print("[yellow]Aborted by user.[/yellow]")
            return
            
    log_entries = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Deleting pages", total=total)
        
        for p in pages_to_delete:
            title = p['title']
            reason = "Bot Cleanup: Confirmed Feb 2020 Spam Wave"
            
            success = False
            retries = 2
            
            while not success and retries >= 0:
                try:
                    if dry_run:
                        status = "DRY-RUN"
                        success = True
                    else:
                        page = site.pages[title]
                        if page.exists:
                            page.delete(reason=reason)
                            status = "DELETED"
                        else:
                            status = "SKIPPED (not found)"
                        success = True
                    
                except Exception as e:
                    error_msg = str(e)
                    if "badtoken" in error_msg or "Invalid token" in error_msg:
                        console.print(f"[yellow]Token expired. Refreshing connection...[/yellow]")
                        site = connect(login=True)
                        retries -= 1
                        time.sleep(1)
                    else:
                        console.print(f"[red]Error deleting {title}: {e}[/red]")
                        status = f"ERROR: {error_msg}"
                        success = True # Stop retrying for non-token errors
            
            log_entries.append({
                "title": title,
                "status": status,
                "timestamp": datetime.now().isoformat()
            })
            
            progress.update(task, advance=1, description=f"{title[:40]}")
            
            if not dry_run and success:
                time.sleep(EDIT_THROTTLE)
                
    return log_entries

def save_removal_log(log_entries, output_dir):
    """Save the removal log to a JSON file."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(output_dir, f"removal_log_{timestamp}.json")
    
    with open(log_path, 'w') as f:
        json.dump(log_entries, f, indent=2)
    
    return log_path

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Delete spam pages from Hackteria wiki")
    parser.add_argument("report", help="Path to the audit JSON report")
    parser.add_argument("--delete", action="store_true", help="Actually perform deletions (default: dry-run)")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of pages to process")
    
    args = parser.parse_args()
    
    console = Console()
    
    if not os.path.exists(args.report):
        console.print(f"[red]Error: Report file not found: {args.report}[/red]")
        sys.exit(1)
        
    data = load_audit_report(args.report)
    spam_pages = [p for p in data['pages'] if p['classification'] == 'SPAM']
    
    if not spam_pages:
        console.print("[green]No SPAM pages found in report. Nothing to do.[/green]")
        sys.exit(0)
        
    site = connect(login=True)
    
    log = delete_spam_pages(site, spam_pages, dry_run=not args.delete, limit=args.limit, force=args.force)
    
    if log:
        log_path = save_removal_log(log, os.path.dirname(args.report))
        console.print(f"\n[bold green]Done![/bold green] Removal log saved to: {log_path}")
