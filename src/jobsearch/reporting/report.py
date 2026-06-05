"""Daily report model, pure builder, and text/markdown/HTML renderers."""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from datetime import date

from jobsearch.reporting.config import ReportingConfig


@dataclass
class RoleBreakdown:
    role: str
    label: str
    high: int = 0
    medium: int = 0


@dataclass
class Opportunity:
    company: str
    role: str
    title: str
    match_score: int
    priority: str
    url: str
    tier: str | None = None
    location: str | None = None


def _to_opportunity(row, config: ReportingConfig) -> Opportunity:
    return Opportunity(
        company=row[0],
        role=config.label(row[1]),
        title=row[2],
        match_score=int(row[3]),
        priority=row[4],
        url=row[5],
        tier=row[6] if len(row) > 6 else None,
        location=row[7] if len(row) > 7 else None,
    )


@dataclass
class DailyReport:
    day: date
    jobs_found_today: int
    roles: list[RoleBreakdown]
    top_opportunities: list[Opportunity]
    all_matches: list[Opportunity] = field(default_factory=list)
    new_or_updated: int = 0  # populated by the notification service
    window_days: int = 1

    @property
    def found_label(self) -> str:
        if self.window_days <= 1:
            return "Jobs Found Today"
        return f"Jobs Found (last {self.window_days} days)"

    # ---- builder --------------------------------------------------------

    @classmethod
    def build(
        cls,
        day: date,
        jobs_found_today: int,
        count_rows: list[tuple[str, str, int]],
        opp_rows: list[tuple],
        config: ReportingConfig,
        match_rows: list[tuple] | None = None,
        window_days: int = 1,
    ) -> DailyReport:
        """Assemble a report from raw DB rows (kept pure for testing).

        count_rows: (role_category, priority, count)
        opp_rows:   (company, role_category, title, match_score, priority, url[, tier])
        match_rows: full list — same shape plus an optional trailing location
        """
        counts: dict[tuple[str, str], int] = {}
        for role, priority, n in count_rows:
            counts[(role, priority)] = counts.get((role, priority), 0) + int(n)

        roles = [
            RoleBreakdown(
                role=r,
                label=config.label(r),
                high=counts.get((r, "HIGH"), 0),
                medium=counts.get((r, "MEDIUM"), 0),
            )
            for r in config.roles
        ]
        return cls(
            day=day,
            jobs_found_today=jobs_found_today,
            roles=roles,
            top_opportunities=[_to_opportunity(r, config) for r in opp_rows],
            all_matches=[_to_opportunity(r, config) for r in (match_rows or [])],
            window_days=window_days,
        )

    # ---- renderers ------------------------------------------------------

    def to_text(self) -> str:
        lines = [
            f"Job Search — Daily Report ({self.day.isoformat()})",
            "=" * 44,
            f"{self.found_label}: {self.jobs_found_today}",
        ]
        if self.new_or_updated:
            lines.append(f"New / updated matches: {self.new_or_updated}")
        lines.append("")
        for rb in self.roles:
            lines.append(f"{rb.label}:")
            lines.append(f"  - High Match:   {rb.high}")
            lines.append(f"  - Medium Match: {rb.medium}")
        lines.append("")
        lines.append("Top Opportunities:")
        if not self.top_opportunities:
            lines.append("  (none)")
        for i, o in enumerate(self.top_opportunities, 1):
            tier = f" · {o.tier}" if o.tier else ""
            lines.append(f"  {i}. {o.company} — {o.title} [{o.role}]{tier}")
            lines.append(f"     score {o.match_score} ({o.priority})  {o.url}")
        if self.all_matches:
            lines.append("")
            lines.append(f"All Matches ({len(self.all_matches)}):")
            for i, o in enumerate(self.all_matches, 1):
                loc = f" — {o.location}" if o.location else ""
                lines.append(
                    f"  {i}. [{o.priority}] {o.match_score}  {o.company} — {o.title} "
                    f"[{o.role}]{loc}"
                )
                lines.append(f"      {o.url}")
        return "\n".join(lines)

    def to_markdown(self) -> str:
        lines = [
            f"*Job Search — Daily Report ({self.day.isoformat()})*",
            f"*{self.found_label}:* {self.jobs_found_today}",
        ]
        if self.new_or_updated:
            lines.append(f"*New / updated matches:* {self.new_or_updated}")
        lines.append("")
        for rb in self.roles:
            lines.append(f"*{rb.label}* — High: {rb.high}, Medium: {rb.medium}")
        lines.append("")
        lines.append("*Top Opportunities:*")
        if not self.top_opportunities:
            lines.append("_none_")
        for i, o in enumerate(self.top_opportunities, 1):
            lines.append(
                f"{i}. [{o.company} — {o.title}]({o.url}) · {o.match_score} ({o.priority})"
            )
        return "\n".join(lines)

    def to_telegram_html(self) -> str:
        """Telegram supports a small HTML subset (b, i, a)."""
        e = html.escape
        lines = [
            f"<b>Job Search — Daily Report ({self.day.isoformat()})</b>",
            f"{self.found_label}: <b>{self.jobs_found_today}</b>",
        ]
        if self.new_or_updated:
            lines.append(f"New / updated matches: <b>{self.new_or_updated}</b>")
        lines.append("")
        for rb in self.roles:
            lines.append(f"<b>{e(rb.label)}</b> — High: {rb.high}, Medium: {rb.medium}")
        lines.append("")
        lines.append("<b>Top Opportunities</b>")
        if not self.top_opportunities:
            lines.append("none")
        for i, o in enumerate(self.top_opportunities, 1):
            lines.append(
                f'{i}. <a href="{e(o.url)}">{e(o.company)} — {e(o.title)}</a> '
                f"· {o.match_score} ({e(o.priority)})"
            )
        if self.all_matches:
            lines.append("")
            lines.append(
                f"<b>All {len(self.all_matches)} matches</b> with links are in the email "
                "and dashboard."
            )
        return "\n".join(lines)

    def to_html(self) -> str:
        """Compact HTML body, used for email and embedded in the dashboard."""
        e = html.escape
        rows = "".join(
            f"<tr><td>{e(rb.label)}</td><td>{rb.high}</td><td>{rb.medium}</td></tr>"
            for rb in self.roles
        )
        opp_rows = "".join(
            f"<tr><td>{i}</td><td>{e(o.company)}</td><td>{e(o.role)}</td>"
            f'<td><a href="{e(o.url)}">{e(o.title)}</a></td>'
            f"<td>{o.match_score}</td><td>{e(o.priority)}</td><td>{e(o.tier or '—')}</td></tr>"
            for i, o in enumerate(self.top_opportunities, 1)
        ) or '<tr><td colspan="7">None</td></tr>'
        all_rows = "".join(
            f"<tr><td>{i}</td><td>{e(o.company)}</td><td>{e(o.role)}</td>"
            f'<td><a href="{e(o.url)}">{e(o.title)}</a></td>'
            f"<td>{e(o.location or '—')}</td><td>{o.match_score}</td>"
            f"<td>{e(o.priority)}</td><td>{e(o.tier or '—')}</td></tr>"
            for i, o in enumerate(self.all_matches, 1)
        ) or '<tr><td colspan="8">None</td></tr>'
        updated = (
            f"<p>New / updated matches: <strong>{self.new_or_updated}</strong></p>"
            if self.new_or_updated
            else ""
        )
        return (
            f"<h2>Job Search — Daily Report ({self.day.isoformat()})</h2>"
            f"<p>{self.found_label}: <strong>{self.jobs_found_today}</strong></p>"
            f"{updated}"
            "<h3>By role</h3>"
            "<table><thead><tr><th>Role</th><th>High Match</th><th>Medium Match</th>"
            f"</tr></thead><tbody>{rows}</tbody></table>"
            "<h3>Top Opportunities</h3>"
            "<table><thead><tr><th>#</th><th>Company</th><th>Role</th><th>Title</th>"
            f"<th>Score</th><th>Priority</th><th>Tier</th></tr></thead>"
            f"<tbody>{opp_rows}</tbody></table>"
            f"<h3>All Matches ({len(self.all_matches)})</h3>"
            "<table><thead><tr><th>#</th><th>Company</th><th>Role</th><th>Title</th>"
            "<th>Location</th><th>Score</th><th>Priority</th><th>Tier</th></tr></thead>"
            f"<tbody>{all_rows}</tbody></table>"
        )
