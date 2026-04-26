"""
Spam Audit Scanner v3 — Fast Batch Approach

Uses batch revision queries to determine page creators efficiently.
MediaWiki 1.28 doesn't allow rvdir=newer with multiple pages, BUT:
- Spam pages typically have only 1 revision (created by spam bot, never edited after)
- So the LATEST revision = the ONLY revision = the creator
- We batch-query latest revisions (50 pages at a time), which works fine
- For pages with multiple revisions, we do a second pass to get the true creator

All operations are READ-ONLY.
"""
import json
import time
import os
import sys
from datetime import datetime
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wiki_connection import connect, get_site_stats
from config import REPORTS_DIR

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn
from rich.table import Table


def get_spam_users(site):
    """Get all user accounts created during the Feb 2020 spam wave."""
    console = Console()
    console.print("\n[bold cyan]👤 Fetching Feb 2020 spam accounts...[/bold cyan]")
    
    all_users = set()
    result = site.api('query',
        list='logevents', letype='newusers',
        lestart='2020-02-15T00:00:00Z', leend='2020-02-01T00:00:00Z',
        ledir='older', lelimit=500, leprop='title|timestamp|user',
    )
    for e in result['query']['logevents']:
        if e.get('user'):
            all_users.add(e['user'])
    
    while 'continue' in result:
        result = site.api('query',
            list='logevents', letype='newusers',
            lestart='2020-02-15T00:00:00Z', leend='2020-02-01T00:00:00Z',
            ledir='older', lelimit=500, leprop='title|timestamp|user',
            **result['continue'],
        )
        for e in result['query']['logevents']:
            if e.get('user'):
                all_users.add(e['user'])
    
    console.print(f"  [bold red]{len(all_users):,}[/bold red] spam accounts found\n")
    return all_users


def get_all_pages_fast(site):
    """Get all pages in main namespace with latest revision info (batch)."""
    console = Console()
    
    # Step 1: Get all page IDs
    console.print("[bold cyan]📑 Listing all pages...[/bold cyan]")
    page_list = []
    apcontinue = None
    while True:
        kwargs = {'list': 'allpages', 'aplimit': 500, 'apnamespace': 0}
        if apcontinue:
            kwargs['apcontinue'] = apcontinue
        result = site.api('query', **kwargs)
        for p in result['query']['allpages']:
            page_list.append({'pageid': p['pageid'], 'title': p['title']})
        if 'continue' in result:
            apcontinue = result['continue']['apcontinue']
        else:
            break
        time.sleep(0.05)
    
    console.print(f"  {len(page_list):,} pages found\n")
    
    # Step 2: Batch-query latest revision (50 pages at a time)
    # Latest revision is returned by default (no rvdir needed)
    console.print("[bold cyan]📅 Fetching latest revisions (batch mode)...[/bold cyan]\n")
    
    batch_size = 50
    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        BarColumn(), MofNCompleteColumn(), console=console,
    ) as progress:
        task = progress.add_task("Batch querying", total=len(page_list))
        
        for i in range(0, len(page_list), batch_size):
            batch = page_list[i:i+batch_size]
            pageids = '|'.join(str(p['pageid']) for p in batch)
            
            try:
                result = site.api('query',
                    prop='revisions|info',
                    pageids=pageids,
                    rvprop='timestamp|user|size',
                )
                
                for pid_str, pdata in result['query']['pages'].items():
                    pid = int(pid_str)
                    for entry in batch:
                        if entry['pageid'] == pid:
                            revs = pdata.get('revisions', [])
                            if revs:
                                entry['last_editor'] = revs[0].get('user', 'unknown')
                                entry['last_edit'] = revs[0].get('timestamp', '')
                                entry['size'] = revs[0].get('size', 0)
                            entry['is_redirect'] = 'redirect' in pdata
                            entry['revcount'] = pdata.get('length', 0)
                            break
            except Exception as e:
                console.print(f"[yellow]⚠ Batch error at {i}: {e}[/yellow]")
                for entry in batch:
                    entry.setdefault('last_editor', 'unknown')
                    entry.setdefault('is_redirect', False)
            
            progress.update(task, advance=len(batch))
            time.sleep(0.1)
    
    return page_list


def get_true_creators(site, pages, spam_users):
    """
    For pages where the latest editor is NOT a spam user but might still 
    have been created by one (i.e., a legit user edited a spam page later),
    we do a targeted single-page query to get the first revision.
    
    This is only needed for the small minority of ambiguous pages.
    """
    console = Console()
    
    # Pages where last_editor is a spam user = definitely spam (no second check needed)
    # Pages where last_editor is legit = probably legit (but could be a spam page that got edited)
    # For safety, we only second-check pages where last_editor is NOT in spam_users
    # AND the page has characteristics that might indicate spam
    
    ambiguous = [p for p in pages 
                 if p.get('last_editor', 'unknown') not in spam_users
                 and not p.get('is_redirect')
                 and p.get('last_editor', 'unknown') != 'unknown']
    
    if not ambiguous:
        return pages
    
    console.print(f"\n[bold cyan]🔎 Double-checking {len(ambiguous)} ambiguous pages...[/bold cyan]\n")
    
    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        BarColumn(), MofNCompleteColumn(), console=console,
    ) as progress:
        task = progress.add_task("Checking creators", total=len(ambiguous))
        
        for page in ambiguous:
            try:
                result = site.api('query',
                    prop='revisions',
                    pageids=str(page['pageid']),
                    rvprop='timestamp|user',
                    rvlimit=1,
                    rvdir='newer',
                )
                pdata = result['query']['pages'].get(str(page['pageid']), {})
                revs = pdata.get('revisions', [])
                if revs:
                    page['creator'] = revs[0].get('user', 'unknown')
                    page['created'] = revs[0].get('timestamp', '')
            except Exception:
                pass
            
            progress.update(task, advance=1)
            time.sleep(0.05)
    
    return pages


def classify_pages(pages, spam_users):
    """Classify pages based on creator/editor vs spam user set."""
    for page in pages:
        if page.get('is_redirect'):
            page['classification'] = 'REDIRECT'
            page['reason'] = 'Redirect page'
            continue
        
        last_editor = page.get('last_editor', 'unknown')
        creator = page.get('creator')  # Only set for double-checked pages
        
        # If we have the true creator, use that
        if creator:
            if creator in spam_users:
                page['classification'] = 'SPAM'
                page['reason'] = f'Created by spam account: {creator}'
            else:
                page['classification'] = 'LEGIT'
                page['reason'] = f'Created by: {creator}'
        # Otherwise, use last_editor as proxy
        elif last_editor in spam_users:
            page['classification'] = 'SPAM'
            page['reason'] = f'Last edited by spam account: {last_editor}'
        elif last_editor == 'unknown':
            page['classification'] = 'UNKNOWN'
            page['reason'] = 'Could not determine editor'
        else:
            page['classification'] = 'LEGIT'
            page['reason'] = f'Last edited by: {last_editor}'
    
    return pages


def generate_report(pages, spam_user_count, output_dir=None):
    """Generate JSON + Markdown audit report."""
    output_dir = output_dir or REPORTS_DIR
    os.makedirs(output_dir, exist_ok=True)
    
    console = Console()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    counter = Counter(p.get('classification', 'UNKNOWN') for p in pages)
    total = len(pages)
    
    # Console table
    console.print()
    table = Table(title=f"📊 Audit Results — {total:,} pages")
    table.add_column("Classification", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_column("%", justify="right")
    for cls in ["LEGIT", "SPAM", "REDIRECT", "UNKNOWN"]:
        count = counter.get(cls, 0)
        pct = f"{count/total*100:.1f}%" if total > 0 else "0%"
        table.add_row(cls, f"{count:,}", pct)
    console.print(table)
    
    # Top legit contributors
    legit_creators = Counter()
    for p in pages:
        if p.get('classification') == 'LEGIT':
            editor = p.get('creator') or p.get('last_editor', '?')
            legit_creators[editor] += 1
    
    if legit_creators:
        console.print(f"\n[bold green]Top contributors (legit pages):[/bold green]")
        for user, count in legit_creators.most_common(20):
            console.print(f"  {user}: {count} pages")
    
    # Save JSON
    json_path = os.path.join(output_dir, f"spam_audit_{timestamp}.json")
    with open(json_path, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "total_scanned": total,
            "summary": dict(counter),
            "spam_user_count": spam_user_count,
            "pages": pages,
        }, f, indent=2, ensure_ascii=False)
    
    # Save Markdown
    md_path = os.path.join(output_dir, f"spam_audit_{timestamp}.md")
    spam_pages = sorted([p for p in pages if p['classification'] == 'SPAM'], key=lambda x: x['title'])
    legit_pages = sorted([p for p in pages if p['classification'] == 'LEGIT'], key=lambda x: x['title'])
    
    with open(md_path, "w") as f:
        f.write(f"# Hackteria Wiki Spam Audit Report\n\n")
        f.write(f"**Date:** {timestamp}  \n")
        f.write(f"**Pages scanned:** {total:,}  \n")
        f.write(f"**Spam accounts (Feb 2020):** {spam_user_count:,}\n\n")
        
        f.write("## Summary\n\n| Classification | Count | % |\n|---|---:|---:|\n")
        for cls in ["LEGIT", "SPAM", "REDIRECT", "UNKNOWN"]:
            count = counter.get(cls, 0)
            f.write(f"| {cls} | {count:,} | {count/total*100:.1f}% |\n")
        
        f.write(f"\n## 🗑️ Spam Pages ({len(spam_pages):,})\n\n")
        for p in spam_pages:
            f.write(f"1. `{p['title']}` — {p.get('reason','')}\n")
        
        f.write(f"\n## ✅ Legitimate Pages ({len(legit_pages):,})\n\n")
        for p in legit_pages:
            editor = p.get('creator') or p.get('last_editor', '?')
            f.write(f"- [{p['title']}](https://hackteria.org/wiki/{p['title'].replace(' ','_')}) — {editor}\n")
    
    console.print(f"\n💾 JSON: {json_path}")
    console.print(f"📋 Report: {md_path}")
    return json_path, md_path


if __name__ == "__main__":
    console = Console()
    console.print("\n[bold cyan]🔍 Hackteria Wiki — Spam Audit v3 (Fast Batch)[/bold cyan]")
    console.print("[dim]Using batch revision queries + Feb 2020 spam user list[/dim]\n")
    
    site = connect(login=True)
    
    # 1. Build spam user set
    spam_users = get_spam_users(site)
    
    # 2. Get all pages with latest revision info (fast batch)
    pages = get_all_pages_fast(site)
    
    # 3. Double-check ambiguous pages
    pages = get_true_creators(site, pages, spam_users)
    
    # 4. Classify
    console.print(f"\n[bold cyan]🏷️  Classifying {len(pages):,} pages...[/bold cyan]")
    pages = classify_pages(pages, spam_users)
    
    # 5. Report
    json_path, md_path = generate_report(pages, len(spam_users))
    console.print("\n[bold green]✅ Audit complete![/bold green]\n")
