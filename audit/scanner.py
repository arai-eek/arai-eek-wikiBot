"""
Wiki Page Scanner — Phase 1 Audit Tool

Scans all pages on the Hackteria wiki and classifies them as:
  - LEGIT:    Real content articles (projects, workshops, documentation)
  - SPAM:     SEO spam, bot-created junk, off-topic commercial content
  - STUB:     Legitimate but very short pages
  - REDIRECT: Wiki redirects
  - UNKNOWN:  Couldn't classify with confidence

Outputs a JSON report + Markdown summary.
All operations are READ-ONLY.
"""
import json
import re
import time
import os
import sys
from datetime import datetime
from collections import Counter

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wiki_connection import connect, get_site_stats
from config import REPORTS_DIR, SPAM_TITLE_PATTERNS, LEGIT_PREFIXES, REQUEST_THROTTLE

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn
from rich.table import Table


# --- Classification Heuristics ---

# Compile spam patterns once
SPAM_RE = [re.compile(p, re.IGNORECASE) for p in SPAM_TITLE_PATTERNS]

# Additional content-based spam signals
SPAM_CONTENT_SIGNALS = [
    r"https?://(?:www\.)?(?:amazon|ebay|aliexpress|shopee|lazada|bet365|casino)",
    r"(?:buy now|order now|click here|limited offer|free shipping|discount code)",
    r"(?:weight loss|male enhancement|erectile dysfunction|anti aging)",
    r"<a\s+href=",  # raw HTML links in wikitext = almost always spam
    r"(?:poker|blackjack|roulette|slot machine|online casino)",
]
SPAM_CONTENT_RE = [re.compile(p, re.IGNORECASE) for p in SPAM_CONTENT_SIGNALS]


def classify_page(title, text, length, is_redirect):
    """
    Classify a single page based on title, content, and metadata.
    
    Returns:
        tuple: (classification: str, confidence: float, reasons: list[str])
    """
    reasons = []
    spam_score = 0
    legit_score = 0
    
    # --- Redirects ---
    if is_redirect:
        return ("REDIRECT", 1.0, ["Page is a redirect"])
    
    # --- Title-based spam detection ---
    for pattern in SPAM_RE:
        if pattern.search(title):
            spam_score += 3
            reasons.append(f"Spam title pattern: {pattern.pattern}")
    
    # Titles that are just numbers/gibberish
    if re.match(r'^[\d\s_\-]+$', title):
        spam_score += 2
        reasons.append("Title is just numbers/gibberish")
    
    # Very long titles with spaces (SEO-style)
    if len(title) > 60 and title.count(' ') > 8:
        spam_score += 1
        reasons.append("Unusually long SEO-style title")
    
    # --- Title-based legitimacy ---
    for prefix in LEGIT_PREFIXES:
        if title.startswith(prefix) or prefix.lower() in title.lower():
            legit_score += 3
            reasons.append(f"Matches legit prefix: {prefix}")
            break
    
    # Known wiki-namespace patterns
    if any(title.startswith(ns) for ns in ["Category:", "Template:", "File:", "User:", "Help:"]):
        legit_score += 2
        reasons.append("Wiki namespace page")
    
    # --- Content-based analysis ---
    if text:
        # Spam content signals
        for pattern in SPAM_CONTENT_RE:
            if pattern.search(text):
                spam_score += 2
                reasons.append(f"Spam content signal: {pattern.pattern[:40]}...")
        
        # Legit content signals  
        if "[[" in text and "]]" in text:  # Internal wiki links
            legit_score += 1
            reasons.append("Contains internal wiki links")
        
        if re.search(r'==\s*.+\s*==', text):  # Section headers
            legit_score += 1
            reasons.append("Has section headers")
        
        if "[[Category:" in text:  # Categorized
            legit_score += 1
            reasons.append("Has categories")
        
        if "{{" in text and "}}" in text:  # Uses templates
            legit_score += 0.5
            reasons.append("Uses templates")
        
        # External link ratio (high ratio = likely spam)
        ext_links = len(re.findall(r'https?://', text))
        int_links = len(re.findall(r'\[\[', text))
        if ext_links > 10 and int_links == 0:
            spam_score += 2
            reasons.append(f"Many external links ({ext_links}) but no internal links")
    
    # --- Length-based ---
    if length < 50:
        if legit_score == 0:
            reasons.append(f"Very short page ({length} bytes)")
    
    # --- Final classification ---
    if spam_score >= 3 and spam_score > legit_score:
        return ("SPAM", min(spam_score / 5.0, 1.0), reasons)
    elif legit_score >= 2:
        if length < 200:
            return ("STUB", min(legit_score / 5.0, 1.0), reasons)
        return ("LEGIT", min(legit_score / 5.0, 1.0), reasons)
    elif length < 100:
        return ("STUB", 0.3, reasons + ["Short page, unclear classification"])
    else:
        return ("UNKNOWN", 0.0, reasons + ["Could not classify with confidence"])


def scan_all_pages(site, limit=None, fetch_content=True):
    """
    Scan all pages and classify them.
    
    Args:
        site: mwclient Site object
        limit: Max pages to scan (None = all)
        fetch_content: Whether to fetch page content for deeper analysis
    
    Returns:
        list[dict]: Classification results for each page
    """
    console = Console()
    results = []
    stats = get_site_stats(site)
    total = stats['pages'] if limit is None else min(limit, stats['pages'])
    
    console.print(f"\n[bold cyan]📡 Scanning {total:,} pages...[/bold cyan]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning pages", total=total)
        
        count = 0
        for page in site.allpages():
            if limit and count >= limit:
                break
            
            title = page.name
            try:
                is_redirect = page.redirect
            except Exception:
                is_redirect = False
            
            # Fetch content for deeper analysis
            text = ""
            length = 0
            if fetch_content and not is_redirect:
                try:
                    text = page.text()
                    length = len(text) if text else 0
                except Exception as e:
                    text = ""
                    length = 0
            
            classification, confidence, reasons = classify_page(
                title, text, length, is_redirect
            )
            
            results.append({
                "title": title,
                "pageid": page.pageid if hasattr(page, 'pageid') else None,
                "classification": classification,
                "confidence": round(confidence, 2),
                "reasons": reasons,
                "length": length,
                "is_redirect": is_redirect,
            })
            
            count += 1
            progress.update(task, advance=1, description=f"[{classification}] {title[:50]}")
            
            # Throttle to be kind to the server
            time.sleep(REQUEST_THROTTLE)
    
    return results


def generate_report(results, output_dir=None):
    """
    Generate audit report from scan results.
    
    Saves:
        - audit_results.json (full data)
        - audit_summary.md (human-readable summary)
    """
    output_dir = output_dir or REPORTS_DIR
    os.makedirs(output_dir, exist_ok=True)
    
    console = Console()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # --- Summary stats ---
    counter = Counter(r["classification"] for r in results)
    total = len(results)
    
    # --- Console output ---
    table = Table(title=f"Audit Results — {total:,} pages scanned")
    table.add_column("Classification", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_column("Percentage", justify="right")
    
    for cls in ["LEGIT", "STUB", "SPAM", "REDIRECT", "UNKNOWN"]:
        count = counter.get(cls, 0)
        pct = f"{count/total*100:.1f}%" if total > 0 else "0%"
        style = {
            "LEGIT": "green", "STUB": "yellow", "SPAM": "red",
            "REDIRECT": "dim", "UNKNOWN": "magenta"
        }.get(cls, "white")
        table.add_row(f"[{style}]{cls}[/{style}]", str(count), pct)
    
    console.print(table)
    
    # --- Save JSON ---
    json_path = os.path.join(output_dir, f"audit_{timestamp}.json")
    with open(json_path, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "total_scanned": total,
            "summary": dict(counter),
            "pages": results,
        }, f, indent=2, ensure_ascii=False)
    console.print(f"\n💾 Full results: [link]{json_path}[/link]")
    
    # --- Save Markdown summary ---
    md_path = os.path.join(output_dir, f"audit_{timestamp}.md")
    
    spam_pages = [r for r in results if r["classification"] == "SPAM"]
    spam_pages.sort(key=lambda x: x["confidence"], reverse=True)
    
    unknown_pages = [r for r in results if r["classification"] == "UNKNOWN"]
    
    with open(md_path, "w") as f:
        f.write(f"# Hackteria Wiki Audit Report\n")
        f.write(f"**Date:** {timestamp}\n")
        f.write(f"**Pages scanned:** {total:,}\n\n")
        
        f.write("## Summary\n\n")
        f.write("| Classification | Count | % |\n")
        f.write("|---|---:|---:|\n")
        for cls in ["LEGIT", "STUB", "SPAM", "REDIRECT", "UNKNOWN"]:
            count = counter.get(cls, 0)
            pct = f"{count/total*100:.1f}" if total > 0 else "0"
            f.write(f"| {cls} | {count:,} | {pct}% |\n")
        
        f.write(f"\n## Top Spam Pages ({len(spam_pages)} total)\n\n")
        for p in spam_pages[:50]:  # Show top 50
            f.write(f"- **{p['title']}** (conf: {p['confidence']}) — {'; '.join(p['reasons'][:2])}\n")
        if len(spam_pages) > 50:
            f.write(f"\n*... and {len(spam_pages)-50} more*\n")
        
        f.write(f"\n## Unknown Pages ({len(unknown_pages)} total)\n\n")
        for p in unknown_pages[:30]:
            f.write(f"- **{p['title']}** ({p['length']} bytes)\n")
        if len(unknown_pages) > 30:
            f.write(f"\n*... and {len(unknown_pages)-30} more*\n")
    
    console.print(f"📋 Markdown summary: [link]{md_path}[/link]")
    
    return json_path, md_path


# --- Main ---
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scan and classify Hackteria wiki pages")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max pages to scan (default: all)")
    parser.add_argument("--no-content", action="store_true",
                        help="Skip fetching page content (faster, less accurate)")
    parser.add_argument("--quick", action="store_true",
                        help="Quick scan: 100 pages, no content fetch")
    args = parser.parse_args()
    
    if args.quick:
        args.limit = 100
        args.no_content = True
    
    console = Console()
    console.print("\n[bold cyan]🔍 Hackteria Wiki Audit Scanner[/bold cyan]\n")
    
    site = connect(login=True)
    results = scan_all_pages(site, limit=args.limit, fetch_content=not args.no_content)
    json_path, md_path = generate_report(results)
    
    console.print("\n[bold green]✅ Audit complete![/bold green]\n")
