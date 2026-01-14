# AI Self-Review

A tool to help engineers write their performance self-reviews by analyzing merged PRs and generating summaries aligned with job requirements.

## Features

- **React Frontend**: Modern UI to manage configuration, view job requirements, and see self-review summaries
- **Flask API**: Backend API to serve configuration, job requirements, and summaries
- **PR Analysis**: Fetches merged PRs from GitHub and generates performance review summaries using AI

## Setup

### Install Dependencies

```bash
make install
```

This will install both Python dependencies (via Poetry) and frontend dependencies (via npm).

### Running the Application

You need to run both the API server and frontend in separate terminals:

**Terminal 1 - Start the API server:**
```bash
make api
```

**Terminal 2 - Start the frontend:**
```bash
make frontend
```

Then open http://localhost:5173 in your browser. The frontend will connect to the API running on port 5000.

## Usage

1. **Configure**: Use the Configuration section to set your GitHub repository and year
2. **View Job Requirements**: See the job requirements document that your work will be evaluated against
3. **View Summary**: See the generated self-review summary based on your merged PRs

## Generating a New Summary

To generate a new self-review summary:

```bash
make review
```

This will:
1. Fetch merged PRs from GitHub for the configured year
2. Generate summaries using AI, aligned with your job requirements
3. Save the results to `self_review_summary.md`

## Project Structure

- `backend/` - Backend Python code
  - `api.py` - Flask backend API
  - `config_loader.py` - Configuration loader utilities
  - `fetch_prs.py` - Script to fetch PRs from GitHub
  - `summarize_prs.py` - Script to generate summaries from PRs
- `frontend/` - React frontend application
- `config.json` - Configuration file (repo and year)
- `role_requirements.md` - Job requirements document
- `self_review_summary.md` - Generated self-review summary

## API Endpoints

- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `GET /api/job-requirements` - Get job requirements content
- `GET /api/summary` - Get self-review summary content

