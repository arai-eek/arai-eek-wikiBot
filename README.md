# 🕷️ Hackteria Wiki Automation Toolkit

A simple, Python-based toolkit for interacting with the [Hackteria Wiki](https://hackteria.org/wiki/). 

## 🛠️ Project Structure

- `wiki_engine/`: The core logic of the bot.
    - `connection.py`: Handles logging into the wiki and connection tests.
    - `config.py`: Loads credentials from `.env`.
    - `example.py`: A simple template showing how to read and list pages.
- `.env`: Your private credentials (do not share!).
- `requirements.txt`: Python dependencies.

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Credentials
Copy `.env.example` to `.env` and fill in your wiki username and password.

### 3. Run the Connection Test
Verify your credentials and connection to the wiki:
```bash
python3 -m wiki_engine.connection
```

### 4. Run the Example
```bash
python3 -m wiki_engine.example
```

---
*Maintained by the Hackteria community.*
