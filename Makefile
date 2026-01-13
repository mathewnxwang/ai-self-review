.PHONY: fetch summarize review

fetch:
	poetry run python fetch_prs.py

summarize:
	poetry run python summarize_prs.py

review: fetch summarize

