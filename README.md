# 🕷️ Hackteria WikiBot (Arai-eek)

An experimental, Python-based toolkit for local-first wiki management. This project focuses on bridging local Markdown drafting with the [Hackteria Wiki](https://hackteria.org/wiki/).

## ⚠️ Prototyping Status: EXPERIMENTAL
This toolkit is currently in a "Bio-Feral" prototyping phase. Expect unresolved issues:
- **Image Uploads**: Automated API uploads are currently unstable/hanging; manual uploads may be required.
- **Conversion Logic**: Uses regex-based patches on `pandoc` output to force specific wiki layouts.
- **Interactive Auth**: Requires a human-in-the-loop for solving security CAPTCHAs.

## 🏔️ Active Prototypes & Demos
- **[[Cyber-Tropicality]]**: Our first live deployment. A visionary page co-created by a human initiator and a multi-model AI ensemble (Gemini 2.0 Flash + DeepSeek V4 Pro).
    - **Live Wiki Page**: [https://hackteria.org/wiki/Cyber-Tropicality](https://hackteria.org/wiki/Cyber-Tropicality)
    - **Local Draft**: `drafts/cyber_tropical.md`

## 🛠️ Project Structure
- `wiki_engine/`: The core automation logic.
    - `converter.py`: Transforms Markdown into wiki-compliant markup.
    - `images.py`: Automatic optimization (Pillow) and upload (curl fallback).
    - `post_draft.py`: The main publishing pipeline.
- `drafts/`: Local staging area for `.md` and `.wiki` previews.
- `SKILL.md`: Behavioral rules and "Institutional Memory" for AI coding assistants.
- `Makefile`: Quick command-line shortcuts (e.g., `make post-draft`).

## 🚀 Getting Started
1. **Install Dependencies**: `pip install -r requirements.txt` and ensure `pandoc` is installed on your system.
2. **Configure**: Fill in your credentials in `.env`.
3. **Draft**: Create a Markdown file in `drafts/`.
4. **Publish**: `make post-draft DRAFT=your_page.md PAGE="Wiki Page Title"`

---
*Developed during the Technobiological Futures Co-Laboratories 2026.*
