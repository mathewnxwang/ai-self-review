# AI Self-Review Generator

A tool to help engineers write their performance self-reviews by analyzing merged PRs and generating summaries aligned with job requirements.

## Features

- **Fully Stateless**: No database, no file storage - everything in the request/response
- **React Frontend**: Modern UI to input configuration and view generated summaries
- **Flask API**: Single endpoint that fetches PRs and generates summaries
- **HTTP Basic Auth**: Simple password protection for access control
- **AI-Powered**: Uses OpenAI to generate structured, requirements-aligned summaries

## Quick Start (Local Development)

### 1. Install Dependencies

```bash
make install
```

### 2. Start the Servers

**Terminal 1 - Start the API server:**
```bash
make api
```

**Terminal 2 - Start the frontend:**
```bash
make frontend
```

### 3. Open the App

Open http://localhost:5173 in your browser.

Default credentials: `admin` / `changeme`

## Usage

1. Enter your **GitHub repository** (e.g., `myorg/myrepo`)
2. Enter the **year** to analyze
3. Enter your **GitHub username** and **Personal Access Token**
4. Enter your **OpenAI API key**
5. Edit the **Role Requirements** to match your job criteria
6. Click **Generate Self-Review**

The app will:
1. Fetch all your merged PRs from that year
2. Group them by label/project
3. Generate AI summaries aligned with your role requirements
4. Display the result (which you can copy)

## Production Deployment

### Environment Variables

Set these environment variables for authentication:

```bash
APP_USERNAME=your-username
APP_PASSWORD=your-secure-password
```

### Deploy to Railway / Render / Fly.io

1. **Build the frontend:**
   ```bash
   cd frontend && npm run build
   ```

2. **Create a `Dockerfile`:**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   # Install poetry and dependencies
   RUN pip install poetry
   COPY pyproject.toml poetry.lock ./
   RUN poetry config virtualenvs.create false && poetry install --no-dev
   
   # Copy application
   COPY backend/ ./backend/
   COPY frontend/dist/ ./frontend/dist/
   
   EXPOSE 5001
   CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5001", "backend.api:app"]
   ```

3. **Deploy** with your platform of choice (Railway, Render, Fly.io, etc.)

4. **Set environment variables** in your deployment platform:
   - `APP_USERNAME`
   - `APP_PASSWORD`

### Security Notes

- User tokens (GitHub, OpenAI) are **never stored** - they're only used for the single request
- HTTP Basic Auth protects the app from unauthorized access
- Consider using HTTPS in production (handled automatically by most platforms)

## Project Structure

- `backend/` - Python Flask API
  - `api.py` - Main API server (single `/api/generate-summary` endpoint)
  - `fetch_prs.py` - Fetches PRs from GitHub API
  - `summarize_prs.py` - Generates summaries using OpenAI
- `frontend/` - React frontend application
- `Makefile` - Build and run commands

## API Endpoint

### POST `/api/generate-summary`

Generates a self-review summary from GitHub PRs.

**Request Body:**
```json
{
  "repo": "owner/repo",
  "year": 2025,
  "github_username": "your-username",
  "github_token": "ghp_xxx",
  "openai_api_key": "sk-xxx",
  "role_requirements": "# Job Requirements\n..."
}
```

**Response:**
```json
{
  "summary": "# Performance Self-Review Summary (2025)\n..."
}
```

**Authentication:** HTTP Basic Auth required.
