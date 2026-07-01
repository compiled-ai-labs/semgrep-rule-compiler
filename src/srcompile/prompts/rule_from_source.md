# Compile a Semgrep rule from a prose source

You are given a prose source document that states a general coding principle — a
coding-guide excerpt or an incident writeup — together with two concrete Python
examples. Derive a single Semgrep rule that enforces the general principle stated
in the source.

The SOURCE is the specification. The two examples only check the rule's edges.
Do not write a rule that merely matches the MUST_FLAG example literally. Capture
the general intent: the rule should flag other code that violates the same
principle, and leave conforming code alone.

## Semgrep YAML primer

A rule is one entry under a top-level `rules:` list. It needs `id`,
`languages: [python]`, `message`, `severity` (ERROR, WARNING, or INFO), and a
pattern block. Use `pattern`, `patterns`, `pattern-either`, `pattern-not`,
`pattern-inside`, or `metavariable-pattern`. Do not use taint mode (`mode: taint`).
Canonical example:

rules:
  - id: subprocess-shell-true
    languages: [python]
    severity: WARNING
    message: subprocess called with shell=True allows shell injection.
    patterns:
      - pattern: subprocess.$FN(..., shell=True, ...)

## SOURCE (the specification — the rule must enforce this general principle)

{{SOURCE}}

## MUST_FLAG (a concrete example the rule must produce at least one finding on)

```python
{{BAD_CODE}}
```

## MUST_NOT_FLAG (a concrete example the rule must produce zero findings on)

```python
{{GOOD_CODE}}
```

## Output

Output only the rule as Semgrep YAML. No prose, no explanation, no code fences.

If the principle in SOURCE genuinely cannot be expressed as a Semgrep pattern —
for example it requires cross-file data flow that Semgrep cannot do without taint
mode — output exactly one line and nothing else:

UNEXPRESSIBLE: <short reason>
{{RETRY_FEEDBACK}}
