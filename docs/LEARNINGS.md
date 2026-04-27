# 🧠 WikiBot Learnings & Insights

This document captures the technical and philosophical "Aha!" moments discovered during the development of the Arai-eek WikiBot. It serves as a guide for others building AI-mediated collaborative tools for MediaWiki.

## 1. The "Ghost Success" Phenomenon (Image Uploads)
**The Problem**: MediaWiki API uploads for binary files often appear to "hang" or timeout at the client side (especially on shared hosting or complex server setups).
**The Discovery**: The server often finishes processing the file (moving it to the final directory, generating thumbnails) *after* it has received the bytes but *before* it can send the JSON "OK" response.
**The Solution**:
- Implement a "Timeout but Check" strategy.
- If the upload request fails or hangs, the bot must immediately check the Wiki's **Upload Log** (`Special:Log/upload`) or query the file existence via API.
- **Never assume failure on a timeout.**

## 2. Link Dualism (Markdown vs. Wiki)
**The Problem**: Wiki links `[[Page Name]]` don't work in standard Markdown previews (VS Code, GitHub), making local drafting feel "blind."
**The Discovery**: Standard Markdown links `[Title](Page_Name)` are natively understood by `pandoc` and converted perfectly to `[[Page Name|Title]]`.
**The Best Practice**:
- Use `[Title](Wiki_Slug)` in local drafts. This provides clickable, navigable previews in the editor while remaining "Wiki-ready."
- Let the conversion engine handle the translation to internal Wiki syntax.

## 3. Section-Level Surgery
**The Problem**: Editing massive wiki pages leads to merge conflicts and accidental data loss.
**The Discovery**: MediaWiki allows editing specific sections via the `&section=N` parameter.
**The Best Practice**:
- Fetch sections individually (`make explore PAGE="..."`).
- Edit only the targeted section in a dedicated draft file.
- Push only that section back.
- This creates a much safer "Human-in-the-Loop" experience where the user only needs to verify a small chunk of text.

## 4. The "Bio-Feral" Philosophy
Developing for a community wiki like Hackteria requires a different mindset than building for a clean corporate API.
- **Resilience over Rigidity**: Scripts should expect failures (lock errors, captchas, timeouts) and provide helpful diagnostics.
- **Transparency**: Always leave an "AI assisted" signature in the edit summary or on-page footer.
- **Verification is King**: The bot is a "drafter," the human is the "editor-in-chief."

---
*Documented during the AI Co-Lab sessions, April 2026.*
