#!/usr/bin/env python3
"""Fetch merged PRs from a configured repository for a specified year."""

import json
import os
import requests
from datetime import datetime
from pathlib import Path

from .config_loader import load_config


def fetch_merged_prs(token: str, username: str, repo: str, year: int) -> list[dict]:
    """Fetch all PRs created by the user and merged in the specified year."""
    url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    all_prs = []
    page = 1
    per_page = 100
    
    # Date range for the specified year
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31, 23, 59, 59)
    
    print(f"Fetching merged PRs for {username} from {repo}...")
    
    while True:
        params = {
            "state": "closed",
            "per_page": per_page,
            "page": page,
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
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
            
            # Parse merge date and filter by year
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
    config = load_config()
    repo = config.repo
    year = config.year
    username = config.github_username
    
    token = os.environ.get("GITHUB_TOKEN")
    
    if not token:
        print("Error: Please set the GITHUB_TOKEN environment variable.")
        return
    
    if not username:
        print("Error: Please set github_username in config.json.")
        return
    
    prs = fetch_merged_prs(token, username, repo, year)
    
    # Sort by merge date
    prs.sort(key=lambda x: x["merged_at"])
    
    # Write output to project root
    output_path = Path(__file__).parent.parent / f"merged_prs_{year}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(prs, f, indent=2)
    
    print(f"\nFound {len(prs)} merged PRs in {year}")
    print(f"Output written to {output_path}")


if __name__ == "__main__":
    main()

