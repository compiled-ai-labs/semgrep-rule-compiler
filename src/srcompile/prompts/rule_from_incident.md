# Compile a Semgrep rule from an incident

You are given one security or reliability incident: a short description, a code
sample that exhibits the problem (MUST_MATCH), and a corrected sample that does
not (MUST_NOT_MATCH). Produce a single Semgrep rule that flags the first and
passes the second.

## Output contract

- Output only the rule, as Semgrep YAML. No prose, no explanation, no code fences.
- One rule under a top-level `rules:` list.
- Python only. Use `pattern`, `patterns`, `pattern-either`, `pattern-not`,
  `pattern-inside`, or `metavariable-pattern`. Do not use taint mode
  (`mode: taint`).
- Include `id`, `languages: [python]`, `message`, `severity`, and the pattern block.
- `message` states the risk in one sentence. `severity` is one of ERROR, WARNING, INFO.
- Make the pattern specific enough that the corrected sample does not match.

## Canonical example

For an incident "subprocess called with shell=True", a correct rule is:

rules:
  - id: subprocess-shell-true
    languages: [python]
    severity: WARNING
    message: subprocess called with shell=True allows shell injection.
    patterns:
      - pattern: subprocess.$FN(..., shell=True, ...)

## This incident

{{DESCRIPTION}}

## MUST_MATCH — the rule must produce at least one finding here

```python
{{BAD_CODE}}
```

## MUST_NOT_MATCH — the rule must produce zero findings here

```python
{{GOOD_CODE}}
```
{{RETRY_FEEDBACK}}
