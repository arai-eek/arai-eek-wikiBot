# 🛠️ Hackteria WikiBot Workflow Shortcuts

.PHONY: test example ai-test clean help

help:
	@echo "Hackteria WikiBot Workflow"
	@echo "--------------------------"
	@echo "make test      - Run connection test"
	@echo "make example   - Run the basic example"
	@echo "make ai-test   - Run the AI example with default topic"
	@echo "make list-drafts - Show all local drafts"
	@echo "make view-draft DRAFT=name - Preview a draft in terminal"
	@echo "make post-draft DRAFT=name PAGE=\"Title\" - Upload the draft"
	@echo "make upload-img IMG=path FILE=name - Upload a local image"
	@echo "make clean     - Remove temporary files"

test:
	python3 -m wiki_engine.connection

example:
	python3 -m wiki_engine.example

ai-test:
	python3 -m wiki_engine.ai_example "Lannafuturism Evolution"

list-drafts:
	@ls -1 drafts/*.wiki drafts/*.md 2>/dev/null || echo "No drafts found."

view-draft:
	@if [ -z "$(DRAFT)" ]; then \
		echo "Usage: make view-draft DRAFT=filename.wiki"; \
		exit 1; \
	fi; \
	cat drafts/$(DRAFT)

post-draft:
	@if [ -z "$(DRAFT)" ] || [ -z "$(PAGE)" ]; then \
		echo "Usage: make post-draft DRAFT=filename PAGE=\"Wiki Title\""; \
		exit 1; \
	fi; \
	python3 -m wiki_engine.post_draft $(DRAFT) "$(PAGE)"

upload-img:
	@if [ -z "$(IMG)" ] || [ -z "$(FILE)" ]; then \
		echo "Usage: make upload-img IMG=media/photo.jpg FILE=TargetName.jpg"; \
		exit 1; \
	fi; \
	python3 -c "from wiki_engine import connect, upload_image; site=connect(login=True); upload_image(site, '$(IMG)', '$(FILE)', 'Uploaded via Makefile shortcut')"

clean:
	rm -f post_ai_content.py
	find . -type d -name "__pycache__" -exec rm -rf {} +
