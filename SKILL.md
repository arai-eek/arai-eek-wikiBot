# 🧠 AI Skill: Hackteria WikiBot Management

This project is a toolkit for automating the [Hackteria Wiki](https://hackteria.org/wiki/). Use this guide to understand how to interact with the bot and the wiki.

## 🏗️ Project Architecture

- **Package**: `wiki_engine`
- **Configuration**: `.env` (contains `BOT_USERNAME`, `BOT_PASSWORD`, `WIKI_URL`)
- **Core Modules**:
    - `wiki_engine.connection`: Handles `connect()` and `get_site_stats()`.
    - `wiki_engine.editor`: Handles `save_page()` and `append_to_page()` with interactive CAPTCHA support.
    - `wiki_engine.config`: Loads settings and handles paths.
    - `wiki_engine.drafter`: Manages local `.md` and `.wiki` drafts.
    - `wiki_engine.converter`: Converts Markdown to MediaWiki using Pandoc.
    - `wiki_engine.images`: Handles image uploads and downloads.

## 🛠️ Key Coding Patterns

### 1. Connecting to the Wiki
Always use the `connect` helper. It handles logging in and verification.
```python
from wiki_engine import connect
site = connect(login=True)
```

### 2. Editing Pages
Use `save_page` for all edits. It includes built-in retry logic for CAPTCHAs.
```python
from wiki_engine import save_page
save_page(site, "Page Title", "New content here", summary="Edit description")
```

### 3. Appending Content
Use `append_to_page` to add logs or updates to the bottom of a page.
```python
from wiki_engine import append_to_page
append_to_page(site, "Log Page", "New log entry", summary="Adding logs")
```

## 🚀 Common Commands

| Task | Command |
| :--- | :--- |
| Test Connection | `make test` |
| Explore Sections | `make explore PAGE="Title"` |
| Fetch Page | `make fetch-page PAGE="Title"` |
| Fetch Section | `python3 -m wiki_engine.fetch_page "Title" --section N` |
| View Draft | `make view-draft DRAFT=name.md` |
| Post Draft | `make post-draft DRAFT=name.md PAGE="Title"` |
| Post Section | `python3 -m wiki_engine.post_draft draft.md "Title" --section N` |
| Upload Image | `make upload-img IMG=path FILE=name.png` |

## 🤖 AI Workflow Strategy (Local-First)

```mermaid
graph TD
    A[Point to Wiki Page] --> B[Fetch Local Markdown]
    B --> C[AI Co-Lab Editing]
    C --> D[Preview in VS Code]
    D --> E{User Approval}
    E -- No --> C
    E -- Yes --> F[Publish to Wiki]
```

When asked to "Modify an existing page" or "Update a section":
1. **Fetch Existing**: Use `make fetch-page PAGE="Title"` or the `--section` flag to get current content.
2. **Draft Locally**: Edit the content in the `drafts/` directory.
3. **Review & Edit**: Inform the user that the draft is ready for manual review/edit in the `drafts/` folder.
3. **Verify**: Use your LLM capabilities to check for formatting errors in the local file.
4. **Mandatory Attribution**: All AI-assisted content must include a standard disclaimer at the bottom of the section/page, including the models used:
   `----`
   `''This content was drafted with the assistance of an AI agent (Arai-eek Bot using Gemini 2.0 Flash and DeepSeek V4 Pro). Please review and verify all information.''`
5. **Publish**: Only after approval, use `python3 -m wiki_engine.post_draft` to upload the finalized content.
6. **Solve**: Handle interactive CAPTCHAs during the publish phase.

## 🖼️ Universal Image Strategy

To maintain a "Local-First" workflow with working previews:

1. **Local Drafting**: Always use standard Markdown syntax in `.md` files:
   `![Caption Text](../media/filename.jpg)`
   * This ensures the image is visible in VS Code and other local Markdown editors.
2. **Auto-Conversion**: The `wiki_engine.converter` automatically:
   - Strips the `../media/` prefix.
   - Translates `![...]` into `[[File:...]]`.
   - Ensures the wiki only receives the final filename (e.g., `File:filename.jpg`).
3. **Consistency**: Do NOT use MediaWiki tags (`[[File:...]]`) directly in Markdown drafts, as it breaks local previews.

## 🧠 Advanced Tips & Lessons Learned

- **Image Optimization**: Always resize images to a maximum width of 1024px and compress them (quality ~85%) before upload. The `wiki_engine.images.optimize_image()` utility handles this automatically.
- **CAPTCHA Persistence**: MediaWiki captchas (like "What year was Hackteria founded?") change frequently. The bot is equipped to prompt for these interactively.
- **Pandoc Dependency**: The conversion workflow requires `pandoc` to be installed on the host system.
- **Wiki Structure**: Always try to link to existing pages like `[[Technobiological Futures Co-Laboratories]]` to maintain the wiki's connective tissue.

---
*This file helps AI coding assistants (Antigravity, Cursor, etc.) understand the project context.*
