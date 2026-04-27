# 🕷️ Hackteria Wiki Automation Toolkit

A simple, Python-based toolkit for interacting with the [Hackteria Wiki](https://hackteria.org/wiki/). 

This project provides a clean base for automating wiki tasks like reading content, updating pages, and managing categories using the `mwclient` library.

## 🚀 Getting Started

### 1. Install Dependencies
Ensure you have Python 3 installed, then run:
```bash
pip install -r requirements.txt
```

### 2. Configure Credentials
Copy `.env.example` to `.env` and fill in your wiki username and password:
```bash
cp .env.example .env
```

*Note: It is recommended to use a dedicated account for automation.*

### 3. Run the Example
Check out `example.py` for a basic demonstration of reading and listing pages:
```bash
python3 example.py
```

## 🛠️ Project Structure

- `wiki_connection.py`: Core utility to handle logging into the wiki.
- `config.py`: Loads environment variables and setting.
- `example.py`: A simple template showing how to read and write pages.

## 📖 Useful Docs
- [mwclient Documentation](https://mwclient.readthedocs.io/)
- [MediaWiki API Reference](https://www.mediawiki.org/wiki/API:Main_page)

---
*Maintained by the Hackteria community.*
