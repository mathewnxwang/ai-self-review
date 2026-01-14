.PHONY: fetch summarize review install api frontend

install:
	poetry install
	cd frontend && npm install

fetch:
	poetry run python -m backend.fetch_prs

summarize:
	poetry run python -m backend.summarize_prs

review: fetch summarize

api:
	poetry run python -m backend.api

frontend:
	cd frontend && npm run dev

