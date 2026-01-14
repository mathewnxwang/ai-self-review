FROM python:3.11-slim

WORKDIR /app

# Install poetry
RUN pip install poetry gunicorn

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (no dev dependencies)
RUN poetry config virtualenvs.create false && poetry install --only main

# Copy application code
COPY backend/ ./backend/
COPY frontend/dist/ ./frontend/dist/

# Expose port
EXPOSE 5001

# Run with gunicorn
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5001", "backend.api:app"]

