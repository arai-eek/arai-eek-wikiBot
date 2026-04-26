# 🕷️ Hackteria WikiBot

An AI-assisted automation toolkit designed to audit, clean, and maintain the [Hackteria.org Wiki](https://hackteria.org/wiki/). 

The project was initiated to address a massive spam contamination where ~80% of the wiki (over 15,000 pages and users) was identified as junk created by automated bots.

## 🚀 The Methodology: "The Feb 2020 Cleanup"

We discovered that the vast majority of spam was injected during a specific window in **February 2020**. Our approach leverages this temporal signal for high-precision removal without risking legitimate community content.

### Phase 1: High-Precision Audit
Instead of unreliable content heuristics, we use a **user-based and date-based classification**:
1.  **Identity Mapping:** We extracted the registration logs for all 15,498 accounts created between Feb 1–15, 2020.
2.  **Creator Verification:** We batch-query every page on the wiki to identify its original creator.
3.  **Classification:** Any page created by a "Feb 2020" account is flagged for deletion. Pages by known contributors (e.g., PaulaPin, Dusjagr) are whitelisted.

### Phase 2: Surgical Cleanup
The cleanup is performed with a focus on server stability and audit trails:
-   **Rate Limiting:** Deletions are throttled to ensure the MediaWiki server remains responsive.
-   **Indefinite Blocking:** Spam accounts are blocked indefinitely, with their ability to create new accounts disabled.
-   **Logging:** Every single deletion and block is recorded in the `reports/` directory for transparency.

---

## 🛠️ Tools & Usage

### 1. Spam Audit (`audit/spam_scanner.py`)
Scans the wiki and generates a JSON/Markdown report of spam vs. legit pages.
```bash
python3 audit/spam_scanner.py
```

### 2. Spam Remover (`cleanup/spam_remover.py`)
Deletes pages based on the audit report.
```bash
# Dry run (safe)
python3 cleanup/spam_remover.py reports/audit_file.json

# Live deletion (with confirmation)
python3 cleanup/spam_remover.py reports/audit_file.json --delete

# Mass deletion (automated)
python3 cleanup/spam_remover.py reports/audit_file.json --delete --force
```

### 3. User Blocker (`cleanup/user_blocker.py`)
Mass-blocks the identified spam accounts.
```bash
python3 cleanup/user_blocker.py reports/audit_file.json --block --force
```

---

## 🔐 Security & Requirements
-   **Python 3.8+**
-   **Dependencies:** `mwclient`, `python-dotenv`, `rich`
-   **Permissions:** Requires a MediaWiki account with `sysop` and `bot` flags.
-   **Environment:** Store credentials in a `.env` file (see `.env.example`).

---
*Created with ❤️ by the Hackteria community and Antigravity AI.*
