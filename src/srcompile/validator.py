"""Validation gates for compiled Semgrep rules.

Each gate is an external check the LLM output must pass before it is written to
rules/. The gates are the entire value proposition: a rule is committed only
when semgrep itself agrees it flags the bad code and passes the good.

Gate 1  output parses as YAML
Gate 2  `semgrep --validate` accepts the rule
Gate 3  the rule produces at least one finding on bad.py  (MUST_MATCH)
Gate 4  the rule produces zero findings on good.py        (MUST_NOT_MATCH)
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class GateResult:
    """Outcome of running all gates on one candidate rule."""

    passed: bool
    failures: list[str] = field(default_factory=list)

    def feedback(self) -> str:
        """The exact gate failures, formatted for feeding back into the prompt."""
        return "\n".join(self.failures)


def parse_yaml(rule_text: str) -> tuple[bool, str]:
    """Gate 1: the output must be valid YAML."""
    try:
        yaml.safe_load(rule_text)
        return True, ""
    except yaml.YAMLError as exc:
        return False, f"Gate 1 failed: YAML parse error: {exc}"


def semgrep_validate(rule_path: Path) -> tuple[bool, str]:
    """Gate 2: `semgrep --validate` must accept the rule."""
    proc = _run_semgrep(["--validate", "--config", str(rule_path)])
    if proc.returncode == 0:
        return True, ""
    detail = (proc.stderr or proc.stdout).strip()
    return False, f"Gate 2 failed: semgrep --validate rejected the rule:\n{detail}"


def semgrep_findings(rule_path: Path, target_path: Path) -> tuple[int, str]:
    """Run the rule against one target. Return (finding_count, error).

    finding_count is -1 when semgrep itself errored (the count is meaningless).
    """
    proc = _run_semgrep(
        ["--config", str(rule_path), "--json", "--quiet", str(target_path)]
    )
    if proc.returncode >= 2:
        return -1, f"semgrep run failed (exit {proc.returncode}):\n{proc.stderr.strip()}"
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return -1, f"could not parse semgrep JSON output: {exc}\n{proc.stderr.strip()}"
    errors = data.get("errors") or []
    if errors:
        msgs = "; ".join(e.get("message", str(e)) for e in errors)
        return -1, f"semgrep reported rule errors: {msgs}"
    return len(data.get("results", [])), ""


def run_gates(rule_text: str, bad_path: Path, good_path: Path) -> GateResult:
    """Run all four gates against one candidate rule.

    Gate 1 is a hard stop: an unparseable rule cannot be written to a temp file
    for the semgrep gates, so we return immediately. Gates 2-4 each append their
    own failure message; all are reported together so one retry can fix several.
    """
    ok, err = parse_yaml(rule_text)
    if not ok:
        return GateResult(passed=False, failures=[err])

    rule_path = _write_temp_rule(rule_text)
    failures: list[str] = []
    try:
        ok, err = semgrep_validate(rule_path)
        if not ok:
            # An invalid rule makes the scan gates meaningless; stop here.
            return GateResult(passed=False, failures=[err])

        bad_count, err = semgrep_findings(rule_path, bad_path)
        if err:
            failures.append(f"Gate 3 error on {bad_path.name}: {err}")
        elif bad_count < 1:
            failures.append(
                f"Gate 3 failed: rule produced 0 findings on {bad_path.name}; "
                f"expected at least 1 (MUST_MATCH)."
            )

        good_count, err = semgrep_findings(rule_path, good_path)
        if err:
            failures.append(f"Gate 4 error on {good_path.name}: {err}")
        elif good_count != 0:
            failures.append(
                f"Gate 4 failed: rule produced {good_count} finding(s) on "
                f"{good_path.name}; expected 0 (MUST_NOT_MATCH)."
            )
    finally:
        rule_path.unlink(missing_ok=True)

    return GateResult(passed=not failures, failures=failures)


def _write_temp_rule(rule_text: str) -> Path:
    with tempfile.NamedTemporaryFile(
        "w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(rule_text)
        return Path(fh.name)


def _run_semgrep(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["semgrep", *args],
        capture_output=True,
        text=True,
    )
