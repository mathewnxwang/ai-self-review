#!/usr/bin/env python3
"""Fetch merged PRs from a configured repository for a specified year."""

import json
import os
import requests
from datetime import datetime
from pathlib import Path

from .models import PullRequest


def fetch_merged_prs(token: str, username: str, repo: str, year: int) -> list[PullRequest]:
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
        
        page_example_printed = False
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
            
            pr_data = PullRequest(
                title=pr["title"],
                description=pr.get("body") or "",
                url=pr["html_url"],
                merged_at=pr["merged_at"],
                labels=[label["name"] for label in pr.get("labels", [])],
                source_repo=repo,
            )
            all_prs.append(pr_data)
            
            # Print first matching PR on each page as example
            if not page_example_printed:
                page_example_printed = True
                print(f"\n  Example PR from page {page}:")
                print(f"    Title: {pr_data.title}")
                print(f"    URL: {pr_data.url}")
                print(f"    Merged: {pr_data.merged_at}")
                print(f"    Labels: {pr_data.labels}")
                desc = pr_data.description
                print(f"    Description: {desc[:100]}..." if len(desc) > 100 else f"    Description: {desc}")
        
        print(f"  Processed page {page} ({len(prs)} PRs)")
        
        page += 1
    
    return all_prs


def main():
    """Interactive CLI for fetching PRs during development."""
    print("=== Fetch Merged PRs (Dev Mode) ===\n")
    
    # Prompt for inputs
    repo = input("Repository (e.g., owner/repo): ").strip()
    if not repo:
        print("Error: Repository is required.")
        return
    
    year_str = input("Year (e.g., 2025): ").strip()
    try:
        year = int(year_str)
    except ValueError:
        print("Error: Year must be a number.")
        return
    
    username = input("GitHub username: ").strip()
    if not username:
        print("Error: GitHub username is required.")
        return
    
    token = input("GitHub token (or press Enter to use GITHUB_TOKEN env var): ").strip()
    if not token:
        token = os.environ.get("GITHUB_TOKEN", "")
    
    if not token:
        print("Error: GitHub token is required (either input or GITHUB_TOKEN env var).")
        return
    
    print()
    prs = fetch_merged_prs(token, username, repo, year)
    
    # Sort by merge date
    prs.sort(key=lambda x: x.merged_at)
    
    # Write output to project root (convert Pydantic models to dicts for JSON serialization)
    output_path = Path(__file__).parent.parent / f"merged_prs_{year}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([pr.model_dump() for pr in prs], f, indent=2)
    
    print(f"\nFound {len(prs)} merged PRs in {year}")
    print(f"Output written to {output_path}")


if __name__ == "__main__":
    main()

