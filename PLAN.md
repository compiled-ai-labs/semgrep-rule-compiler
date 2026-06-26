# Semgrep Rule Compiler — Build Plan

First reference implementation of the Compiled AI paradigm. The LLM runs at compile time to produce Semgrep rules; the scanner runs deterministically at runtime without any model in the path.

## Scope (v0.1)

Take a folder of incidents (each with bad code, good code, and a description), emit Semgrep YAML rules that flag the bad and pass the good.

Out of scope for v0.1:

- Autofix generation
- Languages other than Python
- Taint mode rules (`pattern` / `pattern-either` only)
- SaaS, API, or UI — CLI only
- Model abstraction layer — direct Anthropic SDK call

## Directory layout

```
semgrep-rule-compiler/
├── README.md
├── LICENSE                                  Apache 2.0
├── PLAN.md                                  this file
├── CLAUDE.md                                repo memory
├── pyproject.toml                           uv-managed
├── .github/
│   └── workflows/
│       ├── compile.yml                      runs srcompile, opens PR
│       └── verify.yml                       runs semgrep on bad/good per incident
├── .claude/
│   └── commands/
│       ├── new-spec.md
│       ├── compile.md
│       ├── verify.md
│       └── check-pattern.md
├── src/
│   └── srcompile/
│       ├── __init__.py
│       ├── cli.py                           `srcompile build ./incidents`
│       ├── compiler.py                      prompt + LLM call + retry loop
│       ├── validator.py                     semgrep invocation, verdict check
│       └── prompts/
│           └── rule_from_incident.md
├── incidents/                               the spec
│   ├── 001-jwt-in-logs/
│   │   ├── incident.md
│   │   ├── bad.py
│   │   └── good.py
│   ├── 002-sql-fstring/
│   │   ├── incident.md
│   │   ├── bad.py
│   │   └── good.py
│   └── 003-requests-no-timeout/
│       ├── incident.md
│       ├── bad.py
│       └── good.py
├── rules/                                   the artifact
│   ├── 001-jwt-in-logs.yaml
│   ├── 002-sql-fstring.yaml
│   └── 003-requests-no-timeout.yaml
└── tests/
    └── test_validator.py
```

The `incidents/` folder is the spec. The `rules/` folder is the artifact. Both committed. Reviewer sees the input next to the output.

## The compile loop

```
for each incident folder in spec_dir:
    inputs = read(incident.md, bad.py, good.py)

    for attempt in 1..3:
        prompt = render_template(rule_from_incident.md, inputs, prior_failure=feedback)
        rule_yaml = call_anthropic(prompt)

        gate_1 = parse_yaml(rule_yaml)               # must be valid YAML
        gate_2 = semgrep_validate(rule_yaml)         # `semgrep --validate`
        gate_3 = semgrep_run(rule_yaml, bad.py)      # must FLAG
        gate_4 = semgrep_run(rule_yaml, good.py)     # must NOT flag

        if all passed:
            write rules/<id>.yaml
            break
        else:
            feedback = format_failures(gate_results)

    if still failing after 3 attempts:
        record failure for this incident, write no rule for it, continue to next incident

# after all incidents processed:
print summary (compiled / failed per incident)
if any incident failed:
    exit non-zero
```

### Failure semantics (explicit)

Incidents are independent — one rule per incident. A single incident failing its
gates after 3 retries does **not** abort the run and does **not** discard rules
already written for other incidents. The compiler writes every rule that passes,
skips the rule for any incident that fails, prints a per-incident summary, and
exits non-zero if any incident failed. This keeps `rules/` consistent (every file
present is gate-verified) while never throwing away good work. A missing rule for
an existing incident is itself detectable drift — `verify.yml` flags any incident
folder without a matching artifact.

## Validation gates (non-negotiable)

1. Output parses as valid YAML.
2. `semgrep --validate` accepts the rule.
3. Running the rule against `bad.py` produces at least one finding.
4. Running the rule against `good.py` produces zero findings.

The LLM does not get its output committed unless `semgrep` itself agrees the rule does what it claims.

## Prompt template

Lives at `src/srcompile/prompts/rule_from_incident.md`. Reviewable in PRs separately from code. Carries:

- Concise description of Semgrep YAML rule format with one canonical example.
- The incident description verbatim.
- The bad code block, labeled `MUST_MATCH`.
- The good code block, labeled `MUST_NOT_MATCH`.
- Constraint: output only YAML, no commentary, no code fences.
- On retry: prior attempt plus the validator's exact error message.

## Seed incidents (v0.1)

1. **001-jwt-in-logs** — JWT or other bearer token passed into a logger call. `log.info(f"token={token}")` pattern.
2. **002-sql-fstring** — SQL query constructed with an f-string, then passed to `cursor.execute`. SQL injection risk.
3. **003-requests-no-timeout** — `requests.get(url)` or `requests.post(url, ...)` without a `timeout=` keyword. Service-hang risk.

These are placeholders. Swap in real incidents from production experience when ready.

## Locked decisions

- License: Apache 2.0.
- LLM: Anthropic SDK direct. Model: `claude-opus-4-8` for compile, override via `SRCOMPILE_MODEL` env var.
- Python: 3.11+.
- Package manager: uv.
- Test framework: pytest.

## Meta-verification

`.github/workflows/verify.yml` runs Semgrep against every `incidents/*/bad.py` and `incidents/*/good.py` using the committed rules in `rules/`. If any rule no longer satisfies its gates, CI fails. This is the regression check: detects when a spec changed but the artifact was not recompiled.

## Distribution

- README is the primary surface. Terse, technical, no marketing. Links to the Compiled AI Medium article and the arXiv anchor.
- Cross-link from the Medium article once v0.1 ships.
- r/LLMDevs post after the end-to-end demo works.
- HN once a second `compiled-ai-labs` repo exists to point to.
