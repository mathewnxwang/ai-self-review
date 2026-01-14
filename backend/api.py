#!/usr/bin/env python3
"""Flask API server for the self-review frontend."""

import json
import subprocess
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

from .config_loader import load_config, Config

app = Flask(__name__)
CORS(app)

# Project root is one level up from backend/
BASE_DIR = Path(__file__).parent.parent


@app.route("/api/config", methods=["GET"])
def get_config():
    """Get current configuration."""
    try:
        config = load_config()
        return jsonify({"repo": config.repo, "year": config.year})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/config", methods=["POST"])
def update_config():
    """Update configuration."""
    try:
        data = request.json
        config_path = BASE_DIR / "config.json"
        
        # Validate data
        if "repo" not in data or "year" not in data:
            return jsonify({"error": "Missing required fields: repo, year"}), 400
        
        # Validate year is an integer
        try:
            year = int(data["year"])
        except (ValueError, TypeError):
            return jsonify({"error": "Year must be an integer"}), 400
        
        # Write to config.json
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump({"repo": data["repo"], "year": year}, f, indent=2)
        
        return jsonify({"repo": data["repo"], "year": year})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/job-requirements", methods=["GET"])
def get_job_requirements():
    """Get job requirements content."""
    try:
        requirements_path = BASE_DIR / "role_requirements.md"
        if not requirements_path.exists():
            return jsonify({"content": ""})
        
        with open(requirements_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/job-requirements", methods=["POST"])
def save_job_requirements():
    """Save job requirements content."""
    try:
        data = request.json
        if "content" not in data:
            return jsonify({"error": "Missing required field: content"}), 400
        
        requirements_path = BASE_DIR / "role_requirements.md"
        with open(requirements_path, "w", encoding="utf-8") as f:
            f.write(data["content"])
        
        return jsonify({"message": "Job requirements saved successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/summary", methods=["GET"])
def get_summary():
    """Get self-review summary content."""
    try:
        summary_path = BASE_DIR / "self_review_summary.md"
        if not summary_path.exists():
            return jsonify({"content": ""})
        
        with open(summary_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/secrets", methods=["GET"])
def get_secrets():
    """Get GitHub credentials (without sensitive values)."""
    try:
        secrets_path = BASE_DIR / "secrets.json"
        if not secrets_path.exists():
            return jsonify({
                "github_username": "",
                "github_token": ""
            })
        
        with open(secrets_path, "r", encoding="utf-8") as f:
            secrets = json.load(f)
        
        # Return masked token for display (show last 4 chars)
        github_token = secrets.get("github_token", "")
        masked_token = "•" * max(0, len(github_token) - 4) + github_token[-4:] if len(github_token) > 4 else "•" * len(github_token)
        
        return jsonify({
            "github_username": secrets.get("github_username", ""),
            "github_token": masked_token,
            "has_token": bool(github_token and github_token != "your_github_pat_here")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/secrets", methods=["POST"])
def save_secrets():
    """Save GitHub credentials."""
    try:
        data = request.json
        secrets_path = BASE_DIR / "secrets.json"
        
        # Load existing secrets if they exist (preserve openai_api_key if it exists)
        existing_secrets = {}
        if secrets_path.exists():
            with open(secrets_path, "r", encoding="utf-8") as f:
                existing_secrets = json.load(f)
        
        # Update with new values (only update provided fields)
        if "github_username" in data:
            existing_secrets["github_username"] = data["github_username"]
        if "github_token" in data:
            existing_secrets["github_token"] = data["github_token"]
        # Note: openai_api_key is not configurable via UI, preserve existing value
        
        # Ensure required fields exist
        if "github_token" not in existing_secrets:
            existing_secrets["github_token"] = "your_github_pat_here"
        if "github_username" not in existing_secrets:
            existing_secrets["github_username"] = "your_username_here"
        # openai_api_key must be set manually in secrets.json if not present
        
        # Write to secrets.json
        with open(secrets_path, "w", encoding="utf-8") as f:
            json.dump(existing_secrets, f, indent=2)
        
        return jsonify({"message": "Secrets saved successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate-summary", methods=["POST"])
def generate_summary():
    """Trigger the fetch and summarize process."""
    try:
        output_parts = []
        
        # First, fetch PRs
        fetch_result = subprocess.run(
            ["poetry", "run", "python", "-m", "backend.fetch_prs"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        output_parts.append("=== Fetch PRs ===")
        output_parts.append(fetch_result.stdout)
        if fetch_result.stderr:
            output_parts.append(fetch_result.stderr)
        
        if fetch_result.returncode != 0:
            return jsonify({
                "error": "Failed to fetch PRs",
                "details": fetch_result.stderr,
                "output": "\n".join(output_parts)
            }), 500
        
        # Then, summarize
        summarize_result = subprocess.run(
            ["poetry", "run", "python", "-m", "backend.summarize_prs"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        output_parts.append("\n=== Summarize PRs ===")
        output_parts.append(summarize_result.stdout)
        if summarize_result.stderr:
            output_parts.append(summarize_result.stderr)
        
        if summarize_result.returncode != 0:
            return jsonify({
                "error": "Failed to generate summary",
                "details": summarize_result.stderr,
                "output": "\n".join(output_parts)
            }), 500
        
        return jsonify({
            "message": "Summary generated successfully",
            "output": "\n".join(output_parts)
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Summary generation timed out"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)

