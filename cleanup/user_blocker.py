"""
Spam User Blocker — Phase 2 Cleanup Tool

Loads a spam audit JSON report and blocks users identified as spammers.
Uses indefinite blocking with 'nocreate' (prevents account creation)
and 'hidename' (hides username from logs).

All operations are READ-ONLY unless --block flag is used.
"""
import json
import time
import os
import sys
from datetime import datetime

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wiki_connection import connect
from config import EDIT_THROTTLE

from rich.console import Console
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

def load_audit_report(file_path):
    """Load the audit results from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def block_spam_users(site, users_to_block, dry_run=True, force=False):
    """
    Block a list of spam users on the wiki.
    """
    console = Console()
    total = len(users_to_block)
    mode_str = "[bold yellow]DRY-RUN[/bold yellow]" if dry_run else "[bold red]BLOCK[/bold red]"
    
    console.print(f"\n[bold cyan]🚫 Starting Spam User Blocking ({mode_str} mode)[/bold cyan]")
    console.print(f"Target: {total:,} users\n")
    
    if not dry_run and not force:
        if not Confirm.ask(f"[bold red]CRITICAL:[/bold red] You are about to BLOCK {total:,} users. Proceed?"):
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
        task = progress.add_task("Blocking users", total=total)
        
        for username in users_to_block:
            reason = "Bot Cleanup: Confirmed Feb 2020 Spam Wave"
            
            success = False
            retries = 2
            
            while not success and retries >= 0:
                try:
                    if dry_run:
                        status = "DRY-RUN"
                        success = True
                    else:
                        # MediaWiki API block action
                        site.api('block',
                            user=username,
                            expiry='infinite',
                            reason=reason,
                            nocreate=True,
                            autoblock=True,
                            hidename=True # Hide from logs for cleaner wiki
                        )
                        status = "BLOCKED"
                        success = True
                    
                except Exception as e:
                    error_msg = str(e)
                    if "badtoken" in error_msg or "Invalid token" in error_msg:
                        console.print(f"[yellow]Token expired. Refreshing connection...[/yellow]")
                        site = connect(login=True)
                        retries -= 1
                        time.sleep(1)
                    elif "alreadyblocked" in error_msg:
                        status = "ALREADY BLOCKED"
                        success = True
                    else:
                        console.print(f"[red]Error blocking {username}: {e}[/red]")
                        status = f"ERROR: {error_msg}"
                        success = True
            
            log_entries.append({
                "username": username,
                "status": status,
                "timestamp": datetime.now().isoformat()
            })
            
            progress.update(task, advance=1, description=f"{username[:40]}")
            
            if not dry_run and success:
                # Blocking is also an edit-like action, respect throttle
                time.sleep(0.5) # Blocking is faster but still throttle a bit
                
    return log_entries

def save_block_log(log_entries, output_dir):
    """Save the block log to a JSON file."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(output_dir, f"block_log_{timestamp}.json")
    
    with open(log_path, 'w') as f:
        json.dump(log_entries, f, indent=2)
    
    return log_path

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Block spam users on Hackteria wiki")
    parser.add_argument("report", help="Path to the audit JSON report")
    parser.add_argument("--block", action="store_true", help="Actually perform blocks (default: dry-run)")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    console = Console()
    
    if not os.path.exists(args.report):
        console.print(f"[red]Error: Report file not found: {args.report}[/red]")
        sys.exit(1)
        
    data = load_audit_report(args.report)
    
    # Get unique spam users from the pages list
    # The audit JSON has a 'spam_user_count' but we need the names.
    # Actually, v2/v3 of the scanner saved the list of spam users it found.
    # Let's extract them from the 'pages' data where classification is SPAM
    spam_users = set()
    for p in data['pages']:
        if p['classification'] == 'SPAM':
            spam_users.add(p.get('creator') or p.get('last_editor'))
            
    if not spam_users:
        console.print("[green]No SPAM users identified in report. Nothing to do.[/green]")
        sys.exit(0)
        
    site = connect(login=True)
    
    log = block_spam_users(site, sorted(list(spam_users)), dry_run=not args.block, force=args.force)
    
    if log:
        log_path = save_block_log(log, os.path.dirname(args.report))
        console.print(f"\n[bold green]Done![/bold green] Block log saved to: {log_path}")
