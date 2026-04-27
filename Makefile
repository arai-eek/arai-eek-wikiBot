# 🛠️ Hackteria WikiBot Workflow Shortcuts

.PHONY: test example ai-test clean help list-drafts view-draft post-draft fetch-page explore upload-img

# Use PYTHONPATH to ensure wiki_engine is findable
export PYTHONPATH := $(PYTHONPATH):.

help:
	@echo "Hackteria WikiBot Workflow"
	@echo "--------------------------"
	@echo "make test      - Run connection test"
	@echo "make example   - Run the basic example"
	@echo "make list-drafts - Show all local drafts"
	@echo "make view-draft DRAFT=name - Preview a draft in terminal"
	@echo "make post-draft DRAFT=name PAGE=\"Title\" - Upload the draft"
	@echo "make fetch-page PAGE=\"Title\" - Download a page to workspace/drafts/"
	@echo "make explore PAGE=\"Title\" - List all sections of a page"
	@echo "make upload-img IMG=path FILE=name - Upload a local image"
	@echo "make clean     - Remove temporary files"

test:
	python3 -m wiki_engine.connection

example:
	python3 -m wiki_engine.example

list-drafts:
	@ls -1 workspace/drafts/*.wiki workspace/drafts/*.md 2>/dev/null || echo "No drafts found."

view-draft:
	@if [ -z "$(DRAFT)" ]; then \
		echo "Usage: make view-draft DRAFT=filename.wiki"; \
		exit 1; \
	fi; \
	cat workspace/drafts/$(DRAFT)

post-draft:
	@if [ -z "$(DRAFT)" ] || [ -z "$(PAGE)" ]; then \
		echo "Usage: make post-draft DRAFT=filename PAGE=\"Wiki Title\""; \
		exit 1; \
	fi; \
	python3 tools/publish.py $(DRAFT) "$(PAGE)"

fetch-page:
	@if [ -z "$(PAGE)" ]; then \
		echo "Usage: make fetch-page PAGE=\"Wiki Title\""; \
		exit 1; \
	fi; \
	python3 tools/fetch.py "$(PAGE)"

explore:
	@if [ -z "$(PAGE)" ]; then \
		echo "Usage: make explore PAGE=\"Wiki Title\""; \
		exit 1; \
	fi; \
	python3 tools/explore.py "$(PAGE)"

upload-img:
	@if [ -z "$(IMG)" ] || [ -z "$(FILE)" ]; then \
		echo "Usage: make upload-img IMG=workspace/media/photo.jpg FILE=TargetName.jpg"; \
		exit 1; \
	fi; \
	python3 -c "from wiki_engine import connect, upload_image; site=connect(login=True); upload_image(site, '$(IMG)', '$(FILE)', 'Uploaded via Makefile shortcut')"

clean:
	rm -f post_ai_content.py
	find . -type d -name "__pycache__" -exec rm -rf {} +
