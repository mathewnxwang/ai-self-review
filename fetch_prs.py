#!/usr/bin/env python3
"""Fetch merged PRs from newfront-insurance/python-backend for 2025."""

import json
import requests
from datetime import datetime
from pathlib import Path


def load_secrets():
    """Load GitHub credentials from secrets.json."""
    secrets_path = Path(__file__).parent / "secrets.json"
    if not secrets_path.exists():
        raise FileNotFoundError(
            "secrets.json not found. Please create it with your GitHub token and username."
        )
    with open(secrets_path) as f:
        return json.load(f)


def fetch_merged_prs(token: str, username: str) -> list[dict]:
    """Fetch all PRs created by the user and merged in 2025."""
    repo = "newfront-insurance/python-backend"
    url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    all_prs = []
    page = 1
    per_page = 100
    
    # Date range for 2025
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 12, 31, 23, 59, 59)
    
    print(f"Fetching merged PRs for {username} from {repo}...")
    
    while True:
        params = {
            "state": "closed",
            "per_page": per_page,
            "page": page,
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        prs = response.json()
        if not prs:
            break
        
        for pr in prs:
            # Skip if not merged
            if not pr.get("merged_at"):
                continue
            
            # Check if created by the target user
            author = pr.get("user", {})
            if not author or author.get("login", "").lower() != username.lower():
                continue
            
            # Parse merge date and filter by 2025
            merged_at = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
            merged_at_naive = merged_at.replace(tzinfo=None)
            
            if not (start_date <= merged_at_naive <= end_date):
                continue
            
            all_prs.append({
                "title": pr["title"],
                "description": pr.get("body") or "",
                "url": pr["html_url"],
                "merged_at": pr["merged_at"],
                "labels": [label["name"] for label in pr.get("labels", [])],
            })
        
        print(f"  Processed page {page} ({len(prs)} PRs)")
        page += 1
    
    return all_prs


def main():
    secrets = load_secrets()
    token = secrets["github_token"]
    username = secrets["github_username"]
    
    if token == "your_github_pat_here" or username == "your_username_here":
        print("Error: Please update secrets.json with your actual GitHub token and username.")
        return
    
    prs = fetch_merged_prs(token, username)
    
    # Sort by merge date
    prs.sort(key=lambda x: x["merged_at"])
    
    # Write output
    output_path = Path(__file__).parent / "merged_prs_2025.json"
    with open(output_path, "w") as f:
        json.dump(prs, f, indent=2)
    
    print(f"\nFound {len(prs)} merged PRs in 2025")
    print(f"Output written to {output_path}")


if __name__ == "__main__":
    main()

