"""Optional LLM polish for generated drafts.

Honours the same constraints as earlier phases:
  * structured JSON inputs only — never HTML or the raw job description;
  * a stable, prompt-cached system prompt;
  * thinking disabled and a tight max_tokens, to protect the daily budget.

It only ever *refines* a deterministic draft, and only for jobs that already
passed the generation gate. anthropic is imported lazily.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from jobsearch.application.config import ApplicationConfig, Candidate
from jobsearch.application.models import JobContext


@dataclass
class GenUsage:
    input_tokens: int
    output_tokens: int


def build_system_prompt(candidate: Candidate) -> str:
    return (
        "You refine job-application drafts (cover letters and recruiter outreach). "
        "You are given structured facts about a role and a draft. Improve clarity, "
        "concision, and tailoring while keeping it professional and truthful. Ground "
        "everything ONLY in the provided facts and the draft — never invent experience, "
        "employers, metrics, or skills. Keep cover letters under ~200 words and outreach "
        "messages short. Return ONLY the final text, with no preamble or commentary.\n\n"
        f"Candidate: {candidate.name}"
        + (f" — {candidate.headline}" if candidate.headline else "")
    )


def build_user_message(kind: str, job: JobContext, draft: str) -> str:
    facts = {
        "kind": kind,
        "company": job.company_name,
        "role_category": job.role_category,
        "title": job.title,
        "match_score": job.match_score,
        "matched_skills": job.matched_skills,
        "missing_skills": job.missing_skills,
    }
    return (
        "Job facts (structured):\n"
        + json.dumps(facts, sort_keys=True)
        + "\n\nDraft to refine:\n"
        + draft
    )


def estimate_max_tokens(kind: str) -> int:
    return 700 if kind == "cover_letter" else 400


def polish(
    kind: str,
    job: JobContext,
    draft: str,
    candidate: Candidate,
    config: ApplicationConfig,
) -> tuple[str, GenUsage]:
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=config.model,
        max_tokens=estimate_max_tokens(kind),
        thinking={"type": "disabled"},
        system=[
            {
                "type": "text",
                "text": build_system_prompt(candidate),
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": build_user_message(kind, job, draft)}],
    )
    text = "".join(b.text for b in response.content if b.type == "text").strip() or draft
    usage = GenUsage(
        input_tokens=getattr(response.usage, "input_tokens", 0) or 0,
        output_tokens=getattr(response.usage, "output_tokens", 0) or 0,
    )
    return text, usage
