#!/usr/bin/env python3
"""Summarize merged PRs by label using LLM for performance self-review."""

import json
from collections import defaultdict
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel


class PullRequest(BaseModel):
    title: str
    description: str
    url: str
    merged_at: str
    labels: list[str]

    @property
    def merged_date(self) -> str:
        return self.merged_at[:10]


class Secrets(BaseModel):
    github_token: str
    github_username: str
    openai_api_key: str


def load_prs() -> list[PullRequest]:
    """Load merged PRs from JSON file."""
    prs_path = Path(__file__).parent / "merged_prs_2025.json"
    with open(prs_path, encoding="utf-8") as f:
        data = json.load(f)
    return [PullRequest.model_validate(pr) for pr in data]


def load_secrets() -> Secrets:
    """Load secrets from secrets.json."""
    secrets_path = Path(__file__).parent / "secrets.json"
    with open(secrets_path, encoding="utf-8") as f:
        return Secrets.model_validate(json.load(f))


def group_prs_by_label(prs: list[PullRequest]) -> dict[str, list[PullRequest]]:
    """Group PRs by their labels."""
    grouped: dict[str, list[PullRequest]] = defaultdict(list)
    for pr in prs:
        for label in pr.labels:
            grouped[label].append(pr)
    return dict(grouped)


def format_prs_for_prompt(prs: list[PullRequest]) -> str:
    """Format PRs into a string for the LLM prompt."""
    lines = []
    for pr in prs:
        lines.append(f"## {pr.title}")
        if pr.description:
            lines.append(pr.description)
        lines.append(f"Merged: {pr.merged_date}")
        lines.append("")
    return "\n".join(lines)


def summarize_label(client: OpenAI, label: str, prs: list[PullRequest]) -> str:
    """Summarize all PRs for a given label into high-level bullet points."""
    prs_text = format_prs_for_prompt(prs)

    prompt = f"""You are helping an engineer write their performance self-review. Below are {len(prs)} pull requests they merged in 2025 under the "{label}" project/label.

Analyze these PRs and summarize the key themes, accomplishments, and impact into 3-7 high-level bullet points suitable for a performance review. Focus on:
- Major features or capabilities delivered
- Technical improvements and optimizations
- Process improvements or tooling
- Cross-team collaboration or leadership
- Impact and value delivered

Be specific but concise. Use action verbs. Quantify impact where possible.

PRs:
{prs_text}

Provide the summary as bullet points:"""

    response = client.chat.completions.create(
        model="gpt-5.2",
        max_completion_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content or ""


def main():
    secrets = load_secrets()
    client = OpenAI(api_key=secrets.openai_api_key)

    prs = load_prs()
    grouped = group_prs_by_label(prs)

    print("=" * 60)
    print("PERFORMANCE SELF-REVIEW SUMMARY")
    print("=" * 60)

    summaries = {}
    for label, label_prs in sorted(grouped.items()):
        print(f"\nSummarizing {label} ({len(label_prs)} PRs)...")
        summary = summarize_label(client, label, label_prs)
        summaries[label] = summary

        print(f"\n### {label.upper()} ###")
        print(summary)
        print()

    # Write summaries to file
    output_path = Path(__file__).parent / "self_review_summary.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Performance Self-Review Summary (2025)\n\n")
        for label, summary in summaries.items():
            f.write(f"## {label}\n\n")
            f.write(summary)
            f.write("\n\n")

    print(f"\nSummaries written to {output_path}")


if __name__ == "__main__":
    main()
