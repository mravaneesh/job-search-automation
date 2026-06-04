"""Optional LLM refinement of the interview-likelihood dimension.

Hard constraints honoured here:
  * The model receives ONLY structured JSON (role, title, company, location,
    matched/missing skills, deterministic sub-scores). Never HTML, never the
    raw job description.
  * The stable system prompt (profile + rubric + schema) is prompt-cached so
    repeated runs are cheap.
  * Thinking is disabled and the output is constrained to a small JSON schema,
    keeping output tokens tiny — the whole point of the <20k/day budget.

The pure helpers (build_system_prompt / build_batch_payload / parse_results)
are unit-tested without any network or SDK.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from jobsearch.scoring.models import JobInput, ScoreResult
from jobsearch.scoring.profile import Profile, ScoringConfig

# JSON schema the model must return (one entry per input job).
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "ref": {"type": "integer"},
                    "likelihood": {"type": "integer"},
                    "note": {"type": "string"},
                },
                "required": ["ref", "likelihood"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


@dataclass
class LlmUsage:
    input_tokens: int
    output_tokens: int


def build_system_prompt(profile: Profile, config: ScoringConfig) -> str:
    """Stable, cache-friendly system prompt. No per-request/volatile content."""
    skills = "\n".join(
        f"  - {role}: {', '.join(s)}" for role, s in sorted(profile.skills_by_role.items())
    )
    priorities = ", ".join(f"{r}={t}" for r, t in sorted(profile.role_priority.items()))
    return (
        "You estimate a candidate's likelihood of passing an interview for a "
        "software engineering role, on a 0-100 integer scale.\n\n"
        "Candidate profile:\n"
        f"- Experience: ~{profile.experience_years:g} years\n"
        f"- Role priorities: {priorities}\n"
        f"- Skills by role:\n{skills}\n\n"
        "You receive a JSON array of jobs. Each job includes only structured "
        "fields and pre-computed deterministic sub-scores (0-100). Use them to "
        "judge realistic interview success. Reward strong skill overlap and a "
        "seniority/experience match; penalise large missing-skill gaps and "
        "roles far above the candidate's level. Weight primary-role fit highest, "
        "then secondary, then stretch.\n\n"
        "Return JSON matching the provided schema: one result per input job, "
        "echoing its `ref`, with an integer `likelihood` (0-100) and an optional "
        "`note` of at most 12 words. Do not invent fields or use outside "
        "knowledge beyond what is provided."
    )


def build_batch_payload(items: list[tuple[JobInput, ScoreResult]], profile: Profile) -> list[dict]:
    """Build the compact, deterministic per-job JSON sent to the model."""
    payload = []
    for job, result in items:
        payload.append(
            {
                "ref": job.job_id,
                "role": job.role_category,
                "role_priority": profile.tier_for(job.role_category),
                "title": job.title,
                "company": job.company_name,
                "company_tier": job.company_category,
                "location": job.location,
                "experience_required": job.experience,
                "matched_skills": result.matched_skills,
                "missing_skills": result.missing_skills,
                "sub_scores": {
                    "skill": result.skill_score,
                    "experience": result.experience_score,
                    "seniority": result.seniority_score,
                    "location": result.location_score,
                    "company": result.company_score,
                },
            }
        )
    return payload


def parse_results(text: str) -> dict[int, int]:
    """Parse the model's JSON into {job_id: clamped_likelihood}."""
    data = json.loads(text)
    out: dict[int, int] = {}
    for item in data.get("results", []):
        ref = item.get("ref")
        likelihood = item.get("likelihood")
        if ref is None or likelihood is None:
            continue
        out[int(ref)] = max(0, min(100, int(likelihood)))
    return out


def estimate_max_tokens(batch_size: int) -> int:
    # ~40 output tokens per job (ref + likelihood + short note), with headroom.
    return min(4096, 256 + batch_size * 48)


def score_batch(
    items: list[tuple[JobInput, ScoreResult]],
    profile: Profile,
    config: ScoringConfig,
) -> tuple[dict[int, int], LlmUsage]:
    """Call Claude for one batch. Returns {job_id: likelihood} and token usage.

    anthropic is imported lazily so the rest of the system runs without it.
    """
    import anthropic

    client = anthropic.Anthropic()
    system = build_system_prompt(profile, config)
    payload = build_batch_payload(items, profile)
    user = json.dumps({"jobs": payload}, sort_keys=True)

    response = client.messages.create(
        model=config.model,
        max_tokens=estimate_max_tokens(len(items)),
        thinking={"type": "disabled"},
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
        output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
    )
    text = next((b.text for b in response.content if b.type == "text"), "{}")
    usage = LlmUsage(
        input_tokens=getattr(response.usage, "input_tokens", 0) or 0,
        output_tokens=getattr(response.usage, "output_tokens", 0) or 0,
    )
    return parse_results(text), usage
