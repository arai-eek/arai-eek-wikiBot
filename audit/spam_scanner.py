"""
Spam Scanner v4 — Corrected Creator-Only Rule

Classification rule (strict):
  SPAM  = page's ORIGINAL CREATOR registered Feb 1-15 2020 AND has ≤3 total edits
  LEGIT = everything else

Workflow:
  Phase 1 — Build refined spam user blacklist
             (Feb 2020 registrations with ≤3 edits)
  Phase 2 — Batch fetch latest revision for all pages (fast)
             For pages whose last_editor is a spam user → check first revision
             For all others → LEGIT immediately (safe, no false positives)
  Phase 3 — Fetch first revision for candidates only
             Confirm SPAM only if ORIGINAL CREATOR is in the blacklist
"""

import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wiki_connection import connect

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, MofNCompleteColumn, TextColumn

console = Console()

SPAM_WINDOW_START = "2020-02-03T00:00:00Z"  # confirmed spike start
SPAM_WINDOW_END   = "2020-02-09T23:59:59Z"  # confirmed spike end
MAX_SPAM_EDITS    = 3   # Users with more than this are treated as legit
BATCH_SIZE        = 50


# ─── Phase 1 ────────────────────────────────────────────────────────────────

def build_spam_blacklist(site):
    """
    Fetch all accounts registered Feb 1-15 2020 and filter to those
    with ≤ MAX_SPAM_EDITS total edits. Returns a set of usernames.
    """
    console.print("\n[bold cyan]Phase 1 — Building refined spam blacklist...[/bold cyan]")

    # Get all registrations in the window
    all_feb_users = []
    result = site.api('query', list='logevents', letype='newusers',
                      lestart=SPAM_WINDOW_END, leend=SPAM_WINDOW_START,
                      lelimit=500, ledir='older')
    for e in result['query']['logevents']:
        all_feb_users.append(e.get('user') or e.get('title', '').replace('User:', ''))
    while 'continue' in result:
        result = site.api('query', list='logevents', letype='newusers',
                          lestart=SPAM_WINDOW_END, leend=SPAM_WINDOW_START,
                          lelimit=500, ledir='older', **result['continue'])
        for e in result['query']['logevents']:
            all_feb_users.append(e.get('user') or e.get('title', '').replace('User:', ''))

    all_feb_users = list(set(all_feb_users))
    console.print(f"  Feb 2020 registrations found: {len(all_feb_users):,}")

    # Filter by edit count in batches of 50
    spam_users = set()
    legit_users = set()

    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  BarColumn(), MofNCompleteColumn(), console=console) as prog:
        task = prog.add_task("Checking edit counts", total=len(all_feb_users))
        for i in range(0, len(all_feb_users), 50):
            batch = all_feb_users[i:i+50]
            try:
                res = site.api('query', list='users', ususers='|'.join(batch),
                               usprop='editcount')
                for u in res['query']['users']:
                    name = u.get('name', '')
                    ec = u.get('editcount', 0)
                    if 'missing' in u or 'invalid' in u:
                        pass
                    elif ec <= MAX_SPAM_EDITS:
                        spam_users.add(name)
                    else:
                        legit_users.add(name)
                        console.print(f"  [green]Keeping legit user:[/green] {name} ({ec} edits)")
            except Exception as e:
                console.print(f"  [red]Error checking batch: {e}[/red]")
            prog.update(task, advance=len(batch))

    console.print(f"  Confirmed spam accounts: [red]{len(spam_users):,}[/red]")
    console.print(f"  Protected legit accounts: [green]{len(legit_users)}[/green]")
    return spam_users


# ─── Phase 2 ────────────────────────────────────────────────────────────────

def get_all_pages(site):
    """Fetch all pages in the main namespace (NS 0)."""
    console.print("\n[bold cyan]Phase 2 — Listing all pages...[/bold cyan]")
    pages = []
    result = site.api('query', list='allpages', apnamespace=0,
                      aplimit=500, apfrom='')
    pages.extend(result['query']['allpages'])
    while 'continue' in result:
        result = site.api('query', list='allpages', apnamespace=0,
                          aplimit=500, **result['continue'])
        pages.extend(result['query']['allpages'])
    console.print(f"  {len(pages):,} pages found.")
    return pages


def batch_fetch_latest(site, page_titles):
    """Batch-query latest revision for up to 50 pages at once."""
    result = site.api(
        'query', prop='revisions', titles='|'.join(page_titles),
        rvprop='user|timestamp'
        # Note: rvlimit cannot be used with multiple pages on MW 1.28
        # Default returns the latest revision only, which is what we need
    )
    pages_data = {}
    for pid, pinfo in result['query'].get('pages', {}).items():
        title = pinfo['title']
        revs = pinfo.get('revisions', [])
        if revs:
            pages_data[title] = {
                'last_editor': revs[0].get('user', ''),
                'last_edit':   revs[0].get('timestamp', ''),
            }
    return pages_data


def get_first_revision(site, title):
    """Fetch the very first revision of a page (the original creator)."""
    try:
        result = site.api(
            'query', prop='revisions', titles=title,
            rvprop='user|timestamp', rvlimit=1, rvdir='newer'
        )
        pages = result['query'].get('pages', {})
        for pid, pinfo in pages.items():
            revs = pinfo.get('revisions', [])
            if revs:
                return revs[0].get('user', ''), revs[0].get('timestamp', '')
    except Exception as e:
        console.print(f"  [red]Error fetching first rev for {title}: {e}[/red]")
    return None, None


# ─── Phase 3 ────────────────────────────────────────────────────────────────

def classify_pages(site, pages, spam_users):
    """
    Classify all pages. Returns lists of spam/legit/redirect.
    Only marks SPAM if the ORIGINAL CREATOR is in spam_users.
    """
    console.print("\n[bold cyan]Phase 3 — Classifying pages...[/bold cyan]")

    titles = [p['title'] for p in pages]
    redirects = {p['title'] for p in pages if p.get('redirect') == ''}

    # Step A: batch fetch latest revisions
    latest = {}
    with Progress(SpinnerColumn(), TextColumn("Batch querying latest revisions"),
                  BarColumn(), MofNCompleteColumn(), console=console) as prog:
        task = prog.add_task("", total=len(titles))
        for i in range(0, len(titles), BATCH_SIZE):
            batch = titles[i:i+BATCH_SIZE]
            latest.update(batch_fetch_latest(site, batch))
            prog.update(task, advance=len(batch))

    # Step B: find candidates (last editor is a spam user → need first-rev check)
    candidates = [t for t in titles if latest.get(t, {}).get('last_editor') in spam_users]
    safe_legit = [t for t in titles if t not in candidates]

    console.print(f"\n  Safe legit (last editor not a spam user): [green]{len(safe_legit):,}[/green]")
    console.print(f"  Candidates needing first-rev check:       [yellow]{len(candidates):,}[/yellow]")

    # Step C: check first revision for candidates
    spam_pages = []
    legit_pages = []
    redirect_pages = []

    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  BarColumn(), MofNCompleteColumn(), console=console) as prog:
        task = prog.add_task("Verifying original creators", total=len(candidates))
        for title in candidates:
            creator, created_at = get_first_revision(site, title)
            if creator in spam_users:
                entry = {
                    'title': title,
                    'creator': creator,
                    'created_at': created_at,
                    'last_editor': latest[title]['last_editor'],
                    'classification': 'SPAM'
                }
                if title in redirects:
                    entry['classification'] = 'REDIRECT'
                    redirect_pages.append(entry)
                else:
                    spam_pages.append(entry)
            else:
                legit_pages.append({
                    'title': title,
                    'creator': creator,
                    'last_editor': latest[title]['last_editor'],
                    'classification': 'LEGIT'
                })
            prog.update(task, advance=1, description=title[:50])
            time.sleep(0.05)

    # All safe_legit pages
    for title in safe_legit:
        entry = {
            'title': title,
            'last_editor': latest.get(title, {}).get('last_editor', ''),
            'classification': 'REDIRECT' if title in redirects else 'LEGIT'
        }
        if entry['classification'] == 'REDIRECT':
            redirect_pages.append(entry)
        else:
            legit_pages.append(entry)

    return spam_pages, legit_pages, redirect_pages


# ─── Main ───────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    console.print("\n[bold magenta]🔍 Hackteria Wiki — Spam Audit v4 (Creator-Only)[/bold magenta]")
    console.print(f"Rule: Original creator registered Feb 2020 AND ≤{MAX_SPAM_EDITS} total edits\n")

    site = connect(login=True)

    spam_users  = build_spam_blacklist(site)
    all_pages   = get_all_pages(site)
    spam, legit, redirects = classify_pages(site, all_pages, spam_users)

    # Summary
    total = len(spam) + len(legit) + len(redirects)
    console.print(f"\n[bold]📊 Results — {total:,} pages[/bold]")
    console.print(f"  [red]SPAM:     {len(spam):,}[/red]")
    console.print(f"  [green]LEGIT:    {len(legit):,}[/green]")
    console.print(f"  [dim]REDIRECT: {len(redirects):,}[/dim]")

    # Save report
    os.makedirs('reports', exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    json_path = f'reports/spam_audit_v4_{ts}.json'
    with open(json_path, 'w') as f:
        json.dump({
            'generated_at': ts,
            'spam_user_count': len(spam_users),
            'totals': {'spam': len(spam), 'legit': len(legit), 'redirect': len(redirects)},
            'pages': spam + legit + redirects
        }, f, indent=2)

    # Markdown summary
    md_path = f'reports/spam_audit_v4_{ts}.md'
    with open(md_path, 'w') as f:
        f.write(f"# Hackteria Wiki Spam Audit v4\n\n")
        f.write(f"Generated: {ts}\n\n")
        f.write(f"| Classification | Count |\n|---|---|\n")
        f.write(f"| SPAM | {len(spam)} |\n")
        f.write(f"| LEGIT | {len(legit)} |\n")
        f.write(f"| REDIRECT | {len(redirects)} |\n\n")
        f.write(f"## Spam Pages\n\n")
        for p in spam:
            f.write(f"- [[{p['title']}]] — creator: `{p.get('creator','?')}`\n")

    console.print(f"\n[green]💾 JSON:   {json_path}[/green]")
    console.print(f"[green]📋 Report: {md_path}[/green]")
    console.print("\n[bold green]✅ Audit complete! Review the report before running cleanup.[/bold green]")
