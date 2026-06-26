"""The compiler: turn each incident into a gate-verified Semgrep rule.

The LLM runs here, at compile time. For each incident the compiler renders a
prompt, calls Anthropic, and runs the four validation gates. A rule is written
to rules/ only when every gate passes. Up to three attempts per incident,
feeding the validator's exact error back into the prompt on each retry.

Incidents are independent. A single incident failing its gates after three
attempts does not abort the run and does not discard rules already written for
other incidents.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from anthropic import Anthropic

from srcompile.validator import GateResult, run_gates

MAX_ATTEMPTS = 3
DEFAULT_MODEL = "claude-opus-4-8"
PROMPT_TEMPLATE = Path(__file__).parent / "prompts" / "rule_from_incident.md"


@dataclass
class IncidentResult:
    """What happened when compiling one incident."""

    incident_id: str
    compiled: bool
    attempts: int
    rule_text: str | None = None
    failure: str | None = None


def compile_all(spec_dir: Path, artifact_dir: Path) -> list[IncidentResult]:
    """Compile every incident in spec_dir, writing passing rules to artifact_dir.

    Returns one IncidentResult per incident, in folder order. The caller decides
    the exit code: any incident with compiled=False means the run failed.
    """
    client = Anthropic()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    results: list[IncidentResult] = []
    for folder in sorted(p for p in spec_dir.iterdir() if p.is_dir()):
        if not (folder / "incident.md").exists():
            continue
        result = compile_incident(client, folder)
        if result.compiled and result.rule_text is not None:
            out = artifact_dir / f"{result.incident_id}.yaml"
            out.write_text(result.rule_text.rstrip() + "\n", encoding="utf-8")
        results.append(result)
    return results


def compile_incident(client: Anthropic, folder: Path) -> IncidentResult:
    """Run the three-attempt compile loop for a single incident folder."""
    incident_id = folder.name
    inputs = _read_incident(folder)
    feedback: str | None = None
    last_failure = ""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        prompt = _render_prompt(inputs, feedback)
        rule_text = _call_llm(client, prompt)
        result: GateResult = run_gates(
            rule_text, folder / "bad.py", folder / "good.py"
        )
        if result.passed:
            return IncidentResult(
                incident_id=incident_id,
                compiled=True,
                attempts=attempt,
                rule_text=rule_text,
            )
        feedback = result.feedback()
        last_failure = feedback

    return IncidentResult(
        incident_id=incident_id,
        compiled=False,
        attempts=MAX_ATTEMPTS,
        failure=last_failure,
    )


def _read_incident(folder: Path) -> dict[str, str]:
    return {
        "description": (folder / "incident.md").read_text(encoding="utf-8").strip(),
        "bad_code": (folder / "bad.py").read_text(encoding="utf-8").strip(),
        "good_code": (folder / "good.py").read_text(encoding="utf-8").strip(),
    }


def _render_prompt(inputs: dict[str, str], prior_failure: str | None) -> str:
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    retry_block = ""
    if prior_failure:
        retry_block = (
            "\n## Your previous attempt failed validation\n\n"
            "Fix the rule so it passes. The exact gate errors were:\n\n"
            f"```\n{prior_failure}\n```\n"
        )
    return (
        template.replace("{{DESCRIPTION}}", inputs["description"])
        .replace("{{BAD_CODE}}", inputs["bad_code"])
        .replace("{{GOOD_CODE}}", inputs["good_code"])
        .replace("{{RETRY_FEEDBACK}}", retry_block)
    )


def _call_llm(client: Anthropic, prompt: str) -> str:
    response = client.messages.create(
        model=_model(),
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return _strip_fences(response.content[0].text)


def _model() -> str:
    # `or` rather than a default arg: an env var set to "" must fall back too.
    return os.environ.get("SRCOMPILE_MODEL") or DEFAULT_MODEL


def _strip_fences(text: str) -> str:
    """The prompt forbids code fences; strip them defensively if one slips in."""
    text = text.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()
