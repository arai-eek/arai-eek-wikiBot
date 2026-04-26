# Hackteria Wiki Maintenance Bot

Bot scripts for maintaining the Hackteria wiki.

## 1. Wiki Audit (audit_wiki.py)

Finds potential spam, deleted pages, and orphan pages.

### Usage:

```bash
# Dry run audit
python3 audit_wiki.py --audit spam

# Save results to file
python3 audit_wiki.py --audit spam --output /path/to/report.json
```

## 2. Spam Removal (cleanup/spam_remover.py)

Deletes pages listed in an audit report.

### Usage:

```bash
# Dry run (recommended first)
python3 cleanup/spam_remover.py /path/to/report.json

# Actual deletion
python3 cleanup/spam_remover.py /path/to/report.json --delete

# Force delete (skip confirmation)
python3 cleanup/spam_remover.py /path/to/report.json --delete --force
```
