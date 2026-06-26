"""Tests for the four validation gates.

Gate 1 (YAML parse) runs anywhere. Gates 2-4 shell out to semgrep and are
skipped when semgrep is not on PATH, so the suite still runs on a machine that
only has the Python deps installed.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from srcompile.validator import (
    parse_yaml,
    run_gates,
    semgrep_findings,
    semgrep_validate,
)

requires_semgrep = pytest.mark.skipif(
    shutil.which("semgrep") is None, reason="semgrep not installed"
)

# Valid YAML and a valid semgrep rule: flags eval(...).
VALID_RULE = """\
rules:
  - id: test-eval
    languages: [python]
    severity: WARNING
    message: avoid eval
    pattern: eval(...)
"""

# Valid YAML, but not a valid semgrep rule: no pattern block.
INVALID_RULE = """\
rules:
  - id: no-pattern
    languages: [python]
    severity: WARNING
    message: missing a pattern
"""

BAD_SRC = "result = eval(user_input)\n"
GOOD_SRC = "result = int(user_input)\n"


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


# Gate 1: YAML parse
def test_parse_yaml_accepts_valid():
    ok, err = parse_yaml(VALID_RULE)
    assert ok
    assert err == ""


def test_parse_yaml_rejects_malformed():
    ok, err = parse_yaml("rules: [unclosed")
    assert not ok
    assert "parse" in err.lower()


# Gate 2: semgrep --validate
@requires_semgrep
def test_validate_accepts_well_formed_rule(tmp_path):
    rule = _write(tmp_path, "rule.yaml", VALID_RULE)
    ok, err = semgrep_validate(rule)
    assert ok, err


@requires_semgrep
def test_validate_rejects_rule_without_pattern(tmp_path):
    rule = _write(tmp_path, "rule.yaml", INVALID_RULE)
    ok, _err = semgrep_validate(rule)
    assert not ok


# Gate 3: must flag bad.py
@requires_semgrep
def test_findings_flags_bad_source(tmp_path):
    rule = _write(tmp_path, "rule.yaml", VALID_RULE)
    bad = _write(tmp_path, "bad.py", BAD_SRC)
    count, err = semgrep_findings(rule, bad)
    assert err == ""
    assert count >= 1


# Gate 4: must pass good.py
@requires_semgrep
def test_findings_passes_good_source(tmp_path):
    rule = _write(tmp_path, "rule.yaml", VALID_RULE)
    good = _write(tmp_path, "good.py", GOOD_SRC)
    count, err = semgrep_findings(rule, good)
    assert err == ""
    assert count == 0


# End to end
@requires_semgrep
def test_run_gates_all_pass(tmp_path):
    bad = _write(tmp_path, "bad.py", BAD_SRC)
    good = _write(tmp_path, "good.py", GOOD_SRC)
    result = run_gates(VALID_RULE, bad, good)
    assert result.passed, result.feedback()


@requires_semgrep
def test_run_gates_detects_good_still_matching(tmp_path):
    # The "good" file here also calls eval, so gate 4 must fail.
    bad = _write(tmp_path, "bad.py", BAD_SRC)
    good = _write(tmp_path, "good.py", "value = eval('2')\n")
    result = run_gates(VALID_RULE, bad, good)
    assert not result.passed
    assert any("Gate 4" in f for f in result.failures)


def test_run_gates_fails_on_unparseable_yaml(tmp_path):
    bad = _write(tmp_path, "bad.py", BAD_SRC)
    good = _write(tmp_path, "good.py", GOOD_SRC)
    result = run_gates("rules: [unclosed", bad, good)
    assert not result.passed
    assert any("Gate 1" in f for f in result.failures)
