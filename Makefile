.PHONY: fetch summarize review install api api2 frontend frontend2

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

api2:
	PORT=5002 poetry run python -m backend.api

frontend:
	cd frontend && npm run dev

frontend2:
	cd frontend && API_PORT=5002 npm run dev

