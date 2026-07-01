"""The compiler: turn each spec into a gate-verified Semgrep rule.

The LLM runs here, at compile time. The primary input is a prose source document
(source.md) that states a general principle. Two concrete fixtures (bad.py,
good.py) are demoted to edge checks: they gate the rule but do not define it. The
rule must generalise from the prose, not overfit the fixtures.

For each spec the compiler renders a prompt, calls Anthropic, and runs the four
validation gates. A rule is written only when every gate passes. Up to three
attempts per spec, feeding the validator's exact error back into the prompt.

Specs are independent. A single spec failing its gates after three attempts does
not abort the run and does not discard rules already written for other specs. A
spec the model declares UNEXPRESSIBLE is recorded and skipped, not failed.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from anthropic import Anthropic

from srcompile.validator import GateResult, run_gates

MAX_ATTEMPTS = 3
DEFAULT_MODEL = "claude-opus-4-8"
UNEXPRESSIBLE = "UNEXPRESSIBLE:"
PROMPT_TEMPLATE = Path(__file__).parent / "prompts" / "rule_from_source.md"


@dataclass
class SpecResult:
    """What happened when compiling one spec.

    status is one of:
      "compiled" — all gates passed; rule_text is written to the artifact folder.
      "failed"   — gates still failing after MAX_ATTEMPTS; detail holds the errors.
      "skipped"  — model returned UNEXPRESSIBLE; detail holds the stated reason.
    """

    spec_id: str
    status: str
    attempts: int
    rule_text: str | None = None
    detail: str | None = None


def compile_all(spec_dir: Path, artifact_dir: Path) -> list[SpecResult]:
    """Compile every spec in spec_dir, writing passing rules to artifact_dir.

    Returns one SpecResult per spec, in folder order. The caller decides the exit
    code: any "failed" spec means the run failed. "skipped" specs do not.
    """
    client = Anthropic()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    results: list[SpecResult] = []
    for folder in sorted(p for p in spec_dir.iterdir() if p.is_dir()):
        if not (folder / "source.md").exists():
            continue
        result = compile_spec(client, folder)
        if result.status == "compiled" and result.rule_text is not None:
            out = artifact_dir / f"{result.spec_id}.yaml"
            out.write_text(result.rule_text.rstrip() + "\n", encoding="utf-8")
        results.append(result)
    return results


def compile_spec(client: Anthropic, folder: Path) -> SpecResult:
    """Run the three-attempt compile loop for a single spec folder."""
    spec_id = folder.name
    inputs = _read_spec(folder)
    feedback: str | None = None
    last_failure = ""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        prompt = _render_prompt(inputs, feedback)
        output = _call_llm(client, prompt)

        if output.startswith(UNEXPRESSIBLE):
            reason = output[len(UNEXPRESSIBLE):].strip()
            return SpecResult(
                spec_id=spec_id, status="skipped", attempts=attempt, detail=reason
            )

        result: GateResult = run_gates(
            output, folder / "bad.py", folder / "good.py"
        )
        if result.passed:
            return SpecResult(
                spec_id=spec_id,
                status="compiled",
                attempts=attempt,
                rule_text=output,
            )
        feedback = result.feedback()
        last_failure = feedback

    return SpecResult(
        spec_id=spec_id,
        status="failed",
        attempts=MAX_ATTEMPTS,
        detail=last_failure,
    )


def _read_spec(folder: Path) -> dict[str, str]:
    return {
        "source": (folder / "source.md").read_text(encoding="utf-8").strip(),
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
        template.replace("{{SOURCE}}", inputs["source"])
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
