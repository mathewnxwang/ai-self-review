#!/usr/bin/env python3
"""Shared data models for the self-review application."""

from pydantic import BaseModel


class PullRequest(BaseModel):
    """Model representing a merged pull request."""
    title: str
    description: str
    url: str
    merged_at: str
    labels: list[str]
    source_repo: str = ""

    @property
    def merged_date(self) -> str:
        """Extract the date portion from merged_at timestamp."""
        return self.merged_at[:10]

