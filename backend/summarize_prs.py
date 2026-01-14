#!/usr/bin/env python3
"""Summarize merged PRs by label using LLM for performance self-review."""

import json
from collections import defaultdict
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

from .config_loader import load_config


class PullRequest(BaseModel):
    title: str
    description: str
    url: str
    merged_at: str
    labels: list[str]

    @property
    def merged_date(self) -> str:
        return self.merged_at[:10]


class SummaryBullet(BaseModel):
    """A single summary bullet point with citations."""
    model_config = ConfigDict(
        json_schema_extra={
            "additionalProperties": False
        }
    )
    
    work_done: str = Field(description="Description of what was done")
    significance: str = Field(description="Description of how the work_done aligns with the job requirements and could be represented in a performance review")
    career_area: str = Field(description="The job requirements area this bullet point belongs to, as defined in the role requirements document")
    pr_urls: list[str] = Field(description="List of GitHub PR URLs that support this bullet point")


class SummaryResponse(BaseModel):
    """Structured response containing summary bullet points with citations."""
    model_config = ConfigDict(
        json_schema_extra={
            "additionalProperties": False
        }
    )
    
    bullets: list[SummaryBullet] = Field(description="List of summary bullet points")


class Secrets(BaseModel):
    github_token: str
    github_username: str
    openai_api_key: str


def load_prs(year: int) -> list[PullRequest]:
    """Load merged PRs from JSON file."""
    # Files are in project root, one level up from backend/
    prs_path = Path(__file__).parent.parent / f"merged_prs_{year}.json"
    with open(prs_path, encoding="utf-8") as f:
        data = json.load(f)
    return [PullRequest.model_validate(pr) for pr in data]


def load_secrets() -> Secrets:
    """Load secrets from secrets.json."""
    # secrets.json is in project root, one level up from backend/
    secrets_path = Path(__file__).parent.parent / "secrets.json"
    with open(secrets_path, encoding="utf-8") as f:
        return Secrets.model_validate(json.load(f))


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
            citation_text = ", ".join(f"[{j+1}]({url})" for j, url in enumerate(bullet.pr_urls))
            lines.append(f"- **Work Done:** {bullet.work_done}")
            lines.append(f"  **Significance:**")
            lines.append(f"  {bullet.significance} ({citation_text})")
            if i < len(grouped_by_area[area]) - 1:
                lines.append("")
        lines.append("")
    
    return "\n".join(lines)


def group_prs_by_label(prs: list[PullRequest]) -> dict[str, list[PullRequest]]:
    """Group PRs by their labels."""
    grouped: dict[str, list[PullRequest]] = defaultdict(list)
    for pr in prs:
        if pr.labels:
            for label in pr.labels:
                grouped[label].append(pr)
        else:
            grouped["Unlabeled"].append(pr)
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


def summarize_label(client: OpenAI, label: str, prs: list[PullRequest], year: int, job_requirements: str) -> SummaryResponse:
    """Summarize all PRs for a given label into high-level bullet points with citations, grouped by job requirements areas."""
    prs_text = format_prs_for_prompt(prs)
    pr_urls = [pr.url for pr in prs]

    prompt = f"""You are helping an engineer write their performance self-review. Below are {len(prs)} pull requests they merged in {year} under the "{label}" project/label.

JOB REQUIREMENTS:
{job_requirements}

Analyze these PRs and summarize the key themes, accomplishments, and impact into 3-7 high-level bullet points. For each bullet point, provide:
- **work_done**: A factual description of what was done (e.g., "Built feature X", "Refactored component Y", "Added tests for Z")
- **significance**: How this work aligns with the job requirements above and could be represented in a performance review context. Reference specific aspects of the job requirements that this work demonstrates (e.g., "Demonstrates ownership and impact by delivering end-to-end features that make net positive impact to the business", "Shows commitment to technical craft through high-quality code and reliability improvements", "Highlights teamwork and collaboration by proactively unblocking team members")
- **career_area**: The job requirements area this bullet point belongs to. Determine the appropriate area based on the job requirements document above. Use the exact section heading name from the document (e.g., if the document has a section called "Ownership & Impact", use that exact name)

Focus on:
- Major features or capabilities delivered
- Technical improvements and optimizations
- Process improvements or tooling
- Cross-team collaboration or leadership
- Impact and value delivered

Be specific but concise. Use action verbs. Quantify impact where possible. When describing significance, explicitly connect the work to the job requirements.

For each bullet point, cite the relevant PR URLs that support that point. A bullet point can cite one or more PRs.

PRs:
{prs_text}"""

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
    if not content:
        raise ValueError("Empty response from LLM")
    
    # Parse JSON response into Pydantic model
    try:
        summary = SummaryResponse.model_validate_json(content)
    except Exception as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {e}") from e
    
    # Validate that all cited URLs are from the provided PRs
    all_urls = set(pr_urls)
    for bullet in summary.bullets:
        for url in bullet.pr_urls:
            if url not in all_urls:
                raise ValueError(f"Cited URL {url} is not in the provided PRs")
    
    return summary


def main():
    config = load_config()
    year = config.year
    
    secrets = load_secrets()
    client = OpenAI(api_key=secrets.openai_api_key)
    job_requirements = load_job_requirements()

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

