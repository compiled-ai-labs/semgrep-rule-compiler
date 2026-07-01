# Semgrep Rule Compiler — Build Plan

First reference implementation of the Compiled AI paradigm. The LLM runs at compile time to produce Semgrep rules; the scanner runs deterministically at runtime without any model in the path.

## Scope (v0.1)

Take a folder of specs — each a prose `source.md` (a coding-guide excerpt or an incident writeup) plus a `bad.py`/`good.py` fixture pair — and emit Semgrep YAML rules that enforce the general principle stated in the prose. The fixtures are edge checks: the rule must flag the bad one and pass the good one, but it must generalise from the prose, not overfit the fixtures.

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
│       └── verify.yml                       runs semgrep on bad/good per spec
├── .claude/
│   └── commands/
│       ├── new-spec.md
│       ├── compile.md
│       ├── verify.md
│       └── check-pattern.md
├── src/
│   └── srcompile/
│       ├── __init__.py
│       ├── cli.py                           `srcompile build ./specs`
│       ├── compiler.py                      prompt + LLM call + retry loop
│       ├── validator.py                     semgrep invocation, verdict check
│       └── prompts/
│           └── rule_from_source.md
├── specs/                                   the spec
│   ├── 001-secrets-in-logs/
│   │   ├── source.md                        prose, primary input
│   │   ├── bad.py                           fixture that MUST be flagged
│   │   └── good.py                          fixture that MUST NOT be flagged
│   ├── 002-http-timeout/
│   │   ├── source.md
│   │   ├── bad.py
│   │   └── good.py
│   └── 003-sql-string-building/
│       ├── source.md
│       ├── bad.py
│       └── good.py
├── rules/                                   the artifact
│   ├── 001-secrets-in-logs.yaml
│   ├── 002-http-timeout.yaml
│   └── 003-sql-string-building.yaml
└── tests/
    └── test_validator.py
```

The `specs/` folder is the spec: `source.md` is the primary, human-written input; `bad.py`/`good.py` are validation fixtures. The `rules/` folder is the artifact. Both committed. Reviewer sees the prose, the fixtures, and the rule side by side.

## The compile loop

```
for each spec folder in spec_dir:
    inputs = read(source.md, bad.py, good.py)      # source.md is primary

    for attempt in 1..3:
        prompt = render_template(rule_from_source.md, inputs, prior_failure=feedback)
        output = call_anthropic(prompt)

        if output starts with "UNEXPRESSIBLE:":     # model's refusal path
            record reason, write no rule, mark spec skipped, next spec

        gate_1 = parse_yaml(output)                  # must be valid YAML
        gate_2 = semgrep_validate(output)            # `semgrep --validate`
        gate_3 = semgrep_run(output, bad.py)         # must FLAG
        gate_4 = semgrep_run(output, good.py)        # must NOT flag

        if all passed:
            write rules/<id>.yaml
            break
        else:
            feedback = format_failures(gate_results)

    if still failing after 3 attempts:
        record failure for this spec, write no rule for it, continue to next spec

# after all specs processed:
print summary (compiled / skipped / failed per spec)
if any spec failed:
    exit non-zero
```

### Failure semantics (explicit)

Specs are independent — one rule per spec. A single spec failing its gates after
3 retries does **not** abort the run and does **not** discard rules already
written for other specs. The compiler writes every rule that passes, skips the
rule for any spec that fails, prints a per-spec summary, and exits non-zero if any
spec failed. This keeps `rules/` consistent (every file present is gate-verified)
while never throwing away good work. A missing rule for an existing spec is itself
detectable drift — `verify.yml` flags any spec folder without a matching artifact.

A spec the model declares `UNEXPRESSIBLE` (see the prompt template) is recorded
and reported as **skipped**, not failed. It writes no rule and does not make the
run exit non-zero: the model is telling us Semgrep is the wrong runtime for that
principle, which is information, not an error.

## Validation gates (non-negotiable)

1. Output parses as valid YAML.
2. `semgrep --validate` accepts the rule.
3. Running the rule against `bad.py` produces at least one finding.
4. Running the rule against `good.py` produces zero findings.

The LLM does not get its output committed unless `semgrep` itself agrees the rule does what it claims.

## Prompt template

Lives at `src/srcompile/prompts/rule_from_source.md`. Reviewable in PRs separately from code. Carries:

- Concise description of Semgrep YAML rule format with one canonical example.
- The prose `source.md` verbatim, labeled `SOURCE`, stated to be the specification the rule must enforce.
- The bad code block, labeled `MUST_FLAG` (a concrete example that must match).
- The good code block, labeled `MUST_NOT_FLAG` (a concrete example that must not).
- Instruction: derive a rule that enforces the general principle in `SOURCE`, using the two examples only to check the rule's edges — not a rule that matches the `MUST_FLAG` example literally.
- Constraint: output only YAML, no commentary, no code fences.
- Refusal path: if the intent in `SOURCE` genuinely cannot be expressed as a Semgrep pattern (e.g. it needs cross-file data flow that Semgrep cannot do without taint mode), output exactly `UNEXPRESSIBLE: <reason>` and nothing else.
- On retry: prior attempt plus the validator's exact error message.

## Why prose

Earlier the primary input was a short `incident.md` plus a `bad.py`/`good.py` pair. That is a weak spec: a good-enough rule could in principle be derived from an AST diff of the two samples, with no model needed. If a deterministic diff can produce the artifact, the LLM is not mandatory and the paradigm has no reason to exist.

The prose input fixes this. `source.md` states a *general* principle ("no secret is ever passed to a logging call, in the message or in any argument") that no pair of examples fully pins down. Reading that intent and turning it into a pattern that generalises is exactly the work an LLM does and a diff cannot. The fixtures stay, but demoted to an independent gate: they prove the rule behaves correctly on two known points, they do not define it.

The rule must generalise from the prose, not overfit the fixtures. A rule that passes `bad.py`/`good.py` but ignores the prose's scope is wrong even though it is green.

**Known limitation (v0.1):** the fixtures are not held out — the model sees them while writing the rule, so it can overfit to exactly those two points and still pass the gates. There is no automatic check that the rule captures the prose's full generality. Human review of rule-against-prose is expected on every compile, and is the reason the compiled rule is committed as a reviewable artifact rather than trusted blind.

## Seed specs (v0.1)

1. **001-secrets-in-logs** — coding-guide excerpt: no secret or personal identifier is ever passed to a logging call, in the message or any argument. Fixture: a token interpolated into `log.info` vs. a presence-only log.
2. **002-http-timeout** — incident writeup (INC-1108): every outbound HTTP call must set an explicit `timeout`. Fixture: `requests.get(url)` vs. `requests.get(url, timeout=5)`.
3. **003-sql-string-building** — incident writeup (INC-0997): SQL must use bound parameters, never string building. Fixture: an f-string `execute` vs. a parameterised `execute`.

These are seeds. Swap in real coding standards and incident writeups from production experience when ready.

## Locked decisions

- License: Apache 2.0.
- LLM: Anthropic SDK direct. Model: `claude-opus-4-8` for compile, override via `SRCOMPILE_MODEL` env var.
- Python: 3.11+.
- Package manager: uv.
- Test framework: pytest.

## Meta-verification

`.github/workflows/verify.yml` runs Semgrep against every `specs/*/bad.py` and `specs/*/good.py` using the committed rules in `rules/`. If any rule no longer satisfies its gates, CI fails. This is the regression check: detects when a spec changed but the artifact was not recompiled.

## Distribution

- README is the primary surface. Terse, technical, no marketing. Links to the Compiled AI Medium article and the arXiv anchor.
- Cross-link from the Medium article once v0.1 ships.
- r/LLMDevs post after the end-to-end demo works.
- HN once a second `compiled-ai-labs` repo exists to point to.
