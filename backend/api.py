#!/usr/bin/env python3
"""Flask API server for the self-review frontend - stateless version."""

import logging
import os

from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from .fetch_prs import fetch_merged_prs
from .summarize_prs import load_secrets, summarize_prs_in_memory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
CORS(app)


def check_auth(username: str, password: str) -> bool:
    """Check if username/password combination is valid."""
    expected_user = os.environ.get("APP_USERNAME", "user")
    expected_pass = os.environ.get("APP_PASSWORD", "Newfront!1")
    return username == expected_user and password == expected_pass


@app.before_request
def require_api_auth():
    """Require authentication for API routes only."""
    if request.method == 'OPTIONS':
        return None
    if not request.path.startswith('/api'):
        return None
    
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return jsonify({"error": "Unauthorized"}), 401


# Log all requests
@app.before_request
def log_request_info():
    """Log incoming request details."""
    logger.info("Request: %s %s", request.method, request.path)


@app.after_request
def log_response_info(response):
    """Log response status."""
    logger.info("Response: %s %s - %d", request.method, request.path, response.status_code)
    return response


# Serve frontend
@app.route('/')
def serve_frontend():
    """Serve the frontend index.html."""
    return app.send_static_file('index.html')


@app.route("/api/generate-summary", methods=["POST"])
def generate_summary():
    """
    Generate a self-review summary - fully stateless.
    
    Expects JSON body:
    {
        "repos": ["owner/repo1", "owner/repo2"],
        "year": 2025,
        "github_username": "username",
        "github_token": "ghp_xxx",
        "role_requirements": "# Job Requirements\\n..."
    }
    
    Returns:
    {
        "summary": "# Performance Self-Review Summary...\\n..."
    }
    """
    logger.info("=== Starting generate_summary endpoint ===")
    try:
        logger.info("Parsing request JSON...")
        data = request.json
        if data is None:
            logger.error("Request body is not valid JSON or empty")
            return jsonify({"error": "Request body must be valid JSON"}), 400
        
        logger.info("Request data keys: %s", list(data.keys()))
        
        # Validate required fields
        required_fields = ["repos", "year", "github_username", "github_token", "role_requirements"]
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            logger.warning("Missing required fields: %s", missing)
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
        
        repos = data["repos"]
        if not isinstance(repos, list) or len(repos) == 0:
            logger.warning("Invalid repos field: must be a non-empty list")
            return jsonify({"error": "repos must be a non-empty list"}), 400
        
        year = int(data["year"])
        github_username = data["github_username"]
        github_token = data["github_token"]
        role_requirements = data["role_requirements"]
        
        logger.info("Validated input: repos=%s, year=%d, github_username=%s", repos, year, github_username)
        
        # Load OpenAI API key from secrets.json
        logger.info("Loading secrets...")
        secrets = load_secrets()
        openai_api_key = secrets.openai_api_key
        logger.info("Secrets loaded successfully")
        
        logger.info("Generating summary for %d repos/%d", len(repos), year)
        
        # Step 1: Fetch PRs from GitHub for all repos (in memory)
        logger.info("Fetching PRs from GitHub...")
        all_prs = []
        repos_with_prs = []
        
        for repo in repos:
            logger.info("Fetching PRs from %s...", repo)
            try:
                repo_prs = fetch_merged_prs(
                    token=github_token,
                    username=github_username,
                    repo=repo,
                    year=year
                )
                if repo_prs:
                    # Convert Pydantic models to dicts for summarize_prs_in_memory
                    all_prs.extend([pr.model_dump() for pr in repo_prs])
                    repos_with_prs.append(repo)
                    logger.info("Found %d PRs from %s", len(repo_prs), repo)
                else:
                    logger.info("No PRs found in %s", repo)
            except Exception as e:
                logger.error("Error fetching PRs from %s: %s", repo, str(e), exc_info=True)
                return jsonify({"error": f"Error fetching PRs from {repo}: {str(e)}"}), 500
        
        if not all_prs:
            logger.warning("No PRs found for %s in any repository for %d", github_username, year)
            repos_str = ", ".join(f"**{repo}**" for repo in repos)
            return jsonify({
                "summary": f"# No PRs Found\n\nNo merged PRs found for user **{github_username}** in repositories {repos_str} for year **{year}**."
            })
        
        logger.info("Found %d total PRs across %d repos, generating summary...", len(all_prs), len(repos_with_prs))
        
        # Step 2: Summarize PRs (in memory)
        logger.info("Starting PR summarization with OpenAI...")
        try:
            summary = summarize_prs_in_memory(
                prs=all_prs,
                year=year,
                openai_api_key=openai_api_key,
                role_requirements=role_requirements,
            )
            logger.info("Summarization complete, summary length: %d chars", len(summary))
        except Exception as e:
            logger.error("Error during summarization: %s", str(e), exc_info=True)
            return jsonify({"error": f"Error generating summary: {str(e)}"}), 500
        
        logger.info("=== Summary generated successfully ===")
        return jsonify({"summary": summary})
        
    except ValueError as e:
        logger.error("Validation error: %s", str(e), exc_info=True)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Unexpected error in generate_summary: %s", str(e), exc_info=True)
        return jsonify({"error": str(e)}), 500


# HTTP error handler (for 4xx/5xx errors)
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Handle HTTP exceptions and return JSON."""
    logger.error("HTTP exception: %s - %s", e.code, e.description)
    response = make_response(jsonify({"error": e.description}), e.code)
    response.headers['Content-Type'] = 'application/json'
    return response


# Global error handler for all other exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions."""
    # Pass through HTTP exceptions to the HTTP handler
    if isinstance(e, HTTPException):
        return handle_http_exception(e)
    
    logger.error("Unhandled exception: %s", str(e), exc_info=True)
    response = make_response(jsonify({"error": str(e)}), 500)
    response.headers['Content-Type'] = 'application/json'
    return response


# Specific 500 error handler
@app.errorhandler(500)
def handle_500_error(e):
    """Handle 500 Internal Server Error."""
    logger.error("500 error: %s", str(e), exc_info=True)
    error_msg = str(e) if str(e) else "Internal Server Error"
    response = make_response(jsonify({"error": error_msg}), 500)
    response.headers['Content-Type'] = 'application/json'
    return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    logger.info("Starting Flask server on port %d", port)
    app.run(debug=True, port=port)
