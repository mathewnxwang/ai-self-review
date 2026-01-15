"""Prompts for LLM summarization tasks."""


def get_summarize_prompt(
    num_prs: int,
    year: int,
    job_requirements: str,
    prs_text: str,
) -> str:
    """Generate the prompt for summarizing PRs.
    
    Args:
        num_prs: Number of PRs being summarized
        year: The year for the summary
        job_requirements: The job requirements text
        prs_text: Formatted PRs text
        
    Returns:
        The formatted prompt string
    """
    return f"""You are helping an engineer write their performance self-review. Below are {num_prs} pull requests they merged in {year}.

JOB REQUIREMENTS:
{job_requirements}

Analyze these PRs and summarize the key themes, accomplishments, and impact into 3-7 high-level bullet points. For each bullet point, provide:
- **title**: A 3-5 word bolded title summarizing the bullet point (e.g., "Built Feature X", "Refactored Component Y", "Added Test Coverage")
- **work_done**: A factual description of what was done (e.g., "Built feature X", "Refactored component Y", "Added tests for Z")
- **significance**: How this work aligns with the job requirements above and could be represented in a performance review context. Reference specific aspects of the job requirements that this work demonstrates
- **career_area**: The job requirements area this bullet point belongs to. Determine the appropriate area based on the job requirements document above. Use the exact section heading name from the document (e.g., if the document has a section called "Ownership & Impact", use that exact name)

Be specific but concise. Use action verbs. Quantify impact where possible. When describing significance, explicitly connect the work to the job requirements.

For each bullet point, cite the relevant PRs that support that point. Include the PR title and URL for each citation. A bullet point can cite one or more PRs.

PRs:
{prs_text}"""

