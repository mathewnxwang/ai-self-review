#!/usr/bin/env python3
"""Summarize merged PRs by label using LLM for performance self-review."""

import json
import logging
import os
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

logger = logging.getLogger(__name__)

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

from .models import PullRequest
from .prompts import get_summarize_label_prompt


class PRCitation(BaseModel):
    """A PR citation with title and URL."""
    model_config = ConfigDict(
        json_schema_extra={
            "additionalProperties": False
        }
    )
    
    title: str = Field(description="The title of the PR")
    url: str = Field(description="The GitHub PR URL")


class SummaryBullet(BaseModel):
    """A single summary bullet point with citations."""
    model_config = ConfigDict(
        json_schema_extra={
            "additionalProperties": False
        }
    )
    
    title: str = Field(description="A 3-5 word bolded title summarizing the bullet point (e.g., 'Built Feature X', 'Refactored Component Y', 'Added Test Coverage')")
    work_done: str = Field(description="Description of what was done")
    significance: str = Field(description="Description of how the work_done aligns with the job requirements and could be represented in a performance review")
    career_area: str = Field(description="The job requirements area this bullet point belongs to, as defined in the role requirements document")
    pr_citations: list[PRCitation] = Field(description="List of PR citations (title and URL) that support this bullet point")


class SummaryResponse(BaseModel):
    """Structured response containing summary bullet points with citations."""
    model_config = ConfigDict(
        json_schema_extra={
            "additionalProperties": False
        }
    )
    
    bullets: list[SummaryBullet] = Field(description="List of summary bullet points")


class Secrets(BaseModel):
    openai_api_key: str


def load_prs(year: int) -> list[PullRequest]:
    """Load merged PRs from JSON file."""
    # Files are in project root, one level up from backend/
    prs_path = Path(__file__).parent.parent / f"merged_prs_{year}.json"
    with open(prs_path, encoding="utf-8") as f:
        data = json.load(f)
    return [PullRequest.model_validate(pr) for pr in data]


def load_secrets() -> Secrets:
    """Load secrets from environment variable or secrets.json."""
    # Check for environment variable first (for stateless deployments)
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        return Secrets(openai_api_key=openai_api_key)
    
    # Fall back to secrets.json (for local development)
    secrets_path = Path(__file__).parent.parent / "secrets.json"
    if secrets_path.exists():
        with open(secrets_path, encoding="utf-8") as f:
            return Secrets.model_validate(json.load(f))
    
    raise ValueError("OPENAI_API_KEY environment variable or secrets.json file required")


def load_job_requirements() -> str:
    """Load job requirements content from role_requirements.md."""
    # role_requirements.md is in project root, one level up from backend/
    job_requirements_path = Path(__file__).parent.parent / "role_requirements.md"
    with open(job_requirements_path, encoding="utf-8") as f:
        return f.read()


def format_summary_with_citations(summary_response: SummaryResponse) -> str:
    """Format summary response into markdown with citations, grouped by career area."""
    # Group bullets by career area
    grouped_by_area: dict[str, list[SummaryBullet]] = defaultdict(list)
    for bullet in summary_response.bullets:
        grouped_by_area[bullet.career_area].append(bullet)
    
    # Sort career areas alphabetically for consistent output
    sorted_areas = sorted(grouped_by_area.keys())
    
    lines = []
    for area in sorted_areas:
        lines.append(f"### {area}")
        lines.append("")
        for i, bullet in enumerate(grouped_by_area[area]):
            lines.append(f"- **{bullet.title}**")
            lines.append("")
            lines.append(f"  **Work Done:** {bullet.work_done}")
            lines.append("")
            lines.append("  **Cited PRs:**")
            for citation in bullet.pr_citations:
                lines.append(f"  - [{citation.title}]({citation.url})")
            lines.append("")
            lines.append("  **Significance:**")
            lines.append(f"  {bullet.significance}")
            if i < len(grouped_by_area[area]) - 1:
                lines.append("")
        lines.append("")
    
    return "\n".join(lines)


def group_prs_by_label(prs: list[PullRequest]) -> dict[str, list[PullRequest]]:
    """Group PRs by their labels. Unlabeled PRs are grouped by source_repo."""
    grouped: dict[str, list[PullRequest]] = defaultdict(list)
    for pr in prs:
        if pr.labels:
            for label in pr.labels:
                grouped[label].append(pr)
        else:
            grouped[pr.source_repo or "unlabeled"].append(pr)
    return dict(grouped)


def format_prs_for_prompt(prs: list[PullRequest]) -> str:
    """Format PRs into a string for the LLM prompt."""
    lines = []
    for pr in prs:
        lines.append(f"## {pr.title}")
        if pr.description:
            lines.append(pr.description)
        lines.append(f"Merged: {pr.merged_date}")
        lines.append(f"URL: {pr.url}")
        lines.append("")
    return "\n".join(lines)


def summarize_label(
    client: OpenAI,
    label: str,
    prs: list[PullRequest],
    year: int,
    job_requirements: str,
    max_retries: int = 3,
) -> SummaryResponse:
    """Summarize all PRs for a given label into high-level bullet points with citations, grouped by job requirements areas."""
    prs_text = format_prs_for_prompt(prs)
    pr_urls = [pr.url for pr in prs]

    prompt = get_summarize_label_prompt(
        num_prs=len(prs),
        year=year,
        label=label,
        job_requirements=job_requirements,
        prs_text=prs_text,
    )

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            # Use OpenAI's structured outputs API with Pydantic model (stable API)
            response = client.chat.completions.create(  # type: ignore[call-overload]
                model="gpt-5.2",
                max_completion_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "summary_response",
                        "schema": SummaryResponse.model_json_schema(),
                        "strict": True,
                    },
                },
            )

            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            if not content:
                logger.warning(
                    f"Empty response for {label} (attempt {attempt + 1}/{max_retries}), "
                    f"finish_reason={finish_reason}"
                )
                raise ValueError(f"Empty response from LLM (finish_reason={finish_reason})")
            
            # Parse JSON response into Pydantic model
            summary = SummaryResponse.model_validate_json(content)
            
            # Validate that all cited URLs are from the provided PRs
            all_urls = set(pr_urls)
            for bullet in summary.bullets:
                for citation in bullet.pr_citations:
                    if citation.url not in all_urls:
                        raise ValueError(f"Cited URL {citation.url} is not in the provided PRs")
            
            return summary
            
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # exponential backoff: 1s, 2s, 4s
                logger.warning(f"Retry {attempt + 1}/{max_retries} for {label} after error: {e}. Waiting {wait_time}s...")
                time.sleep(wait_time)
    
    raise ValueError(f"Failed to summarize {label} after {max_retries} attempts: {last_error}")


def group_prs_by_repo(prs: list[PullRequest]) -> dict[str, list[PullRequest]]:
    """Group PRs by their source repository."""
    grouped: dict[str, list[PullRequest]] = defaultdict(list)
    for pr in prs:
        repo = pr.source_repo or "unknown"
        grouped[repo].append(pr)
    return dict(grouped)


def group_prs_by_label_only(prs: list[PullRequest]) -> dict[str, list[PullRequest]]:
    """Group PRs by their labels only. Unlabeled PRs go to 'unlabeled'."""
    grouped: dict[str, list[PullRequest]] = defaultdict(list)
    for pr in prs:
        if pr.labels:
            for label in pr.labels:
                grouped[label].append(pr)
        else:
            grouped["unlabeled"].append(pr)
    return dict(grouped)


def summarize_prs_in_memory(
    prs: list[dict],
    year: int,
    openai_api_key: str,
    role_requirements: str,
) -> str:
    """
    Summarize PRs in memory without file I/O.
    
    PRs are batched first by source_repo, then by label within each repo.
    
    Args:
        prs: List of PR dictionaries with title, description, url, merged_at, labels, source_repo
        year: The year for the summary
        openai_api_key: OpenAI API key
        role_requirements: Job requirements text
        
    Returns:
        Markdown formatted summary string
    """
    client = OpenAI(api_key=openai_api_key)
    
    # Convert dicts to PullRequest objects
    pr_objects = [PullRequest.model_validate(pr) for pr in prs]
    
    # First group by repo, then by label within each repo
    grouped_by_repo = group_prs_by_repo(pr_objects)
    
    # Structure: {repo: {label: [prs]}}
    batches: dict[str, dict[str, list[PullRequest]]] = {}
    for repo, repo_prs in grouped_by_repo.items():
        batches[repo] = group_prs_by_label_only(repo_prs)
    
    # Flatten batches into a list of tasks: [(repo, label, prs), ...]
    tasks: list[tuple[str, str, list[PullRequest]]] = []
    for repo, labels in batches.items():
        for label, label_prs in labels.items():
            tasks.append((repo, label, label_prs))
    
    def process_batch(task: tuple[str, str, list[PullRequest]]) -> tuple[str, str, str]:
        repo, label, label_prs = task
        batch_key = f"{repo}/{label}"
        logger.info(f"Processing batch: {batch_key} ({len(label_prs)} PRs)")
        summary_response = summarize_label(client, batch_key, label_prs, year, role_requirements)
        formatted_summary = format_summary_with_citations(summary_response)
        logger.info(f"Completed batch: {batch_key}")
        return repo, label, formatted_summary
    
    # Process batches concurrently
    summaries: dict[str, dict[str, str]] = defaultdict(dict)
    with ThreadPoolExecutor(max_workers=min(len(tasks), 10)) as executor:
        futures = {executor.submit(process_batch, task): task for task in tasks}
        for future in as_completed(futures):
            repo, label, formatted_summary = future.result()
            summaries[repo][label] = formatted_summary
    
    # Build final markdown output grouped by repo then label
    lines = []
    for repo in sorted(summaries.keys()):
        lines.append(f"## {repo}")
        lines.append("")
        for label, summary in sorted(summaries[repo].items()):
            lines.append(f"### {label}")
            lines.append("")
            lines.append(summary)
            lines.append("")
    
    return "\n".join(lines)


def main():
    """Interactive CLI for summarizing PRs during development."""
    print("=== Summarize PRs (Dev Mode) ===\n")
    
    # Prompt for year
    year_str = input("Year (e.g., 2025): ").strip()
    try:
        year = int(year_str)
    except ValueError:
        print("Error: Year must be a number.")
        return
    
    secrets = load_secrets()
    client = OpenAI(api_key=secrets.openai_api_key)
    job_requirements = load_job_requirements()

    print(f"\nLoading PRs from merged_prs_{year}.json...")
    prs = load_prs(year)
    grouped = group_prs_by_label(prs)

    print("=" * 60)
    print("PERFORMANCE SELF-REVIEW SUMMARY")
    print("=" * 60)

    summaries = {}
    for label, label_prs in sorted(grouped.items()):
        print(f"\nSummarizing {label} ({len(label_prs)} PRs)...")
        summary_response = summarize_label(client, label, label_prs, year, job_requirements)
        
        # Format summary with citations
        formatted_summary = format_summary_with_citations(summary_response)
        summaries[label] = formatted_summary

        print(f"\n### {label.upper()} ###")
        print(formatted_summary)
        print()

    # Write summaries to file in project root
    output_path = Path(__file__).parent.parent / "self_review_summary.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Performance Self-Review Summary ({year})\n\n")
        for label, summary in summaries.items():
            f.write(f"## {label}\n\n")
            f.write(summary)
            f.write("\n\n")

    print(f"\nSummaries written to {output_path}")


if __name__ == "__main__":
    main()
