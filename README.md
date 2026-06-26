# semgrep-rule-compiler

Compile postmortems and code samples into Semgrep rules. An LLM runs at compile
time to turn a folder of incidents into Semgrep YAML. The scanner runs at
runtime with no model in the path. A rule is only written when Semgrep itself
confirms it flags the bad code and passes the good.

## Why

LLMs are good at drafting a Semgrep rule from an example and bad at being
trusted with it. The usual answer — paste code into a chat, copy the rule out,
hope — has no check that the rule does what it claims. This repo puts the model
behind a gate: the rule is generated offline, validated against the exact bad
and good samples it was built from, and committed as a plain file. The thing you
run in CI is Semgrep, deterministic and auditable, not a model. Background:
["Compiled AI: Engineering Deterministic LLM Systems"](https://medium.com/@boristeplitsky)
(placeholder link).

## The five-part flow

1. **Spec** — `incidents/<id>/` with `incident.md`, `bad.py`, `good.py`. Human-maintained.
2. **Compiler** — `src/srcompile/compiler.py`. Calls Anthropic with a templated prompt. Offline.
3. **Validation gates** — `src/srcompile/validator.py`. Parse, `semgrep --validate`, flag bad, pass good.
4. **Artifact** — `rules/<id>.yaml`. Committed, reviewable, pinned by consumers.
5. **Runtime** — `semgrep`. Deterministic. No LLM in this path.

## Try it

```bash
uv sync
export ANTHROPIC_API_KEY=sk-...
uv run srcompile build ./incidents
```

This writes one `rules/<id>.yaml` per incident that passes all four gates, and
exits non-zero if any incident fails. Review each rule before committing.
Verifying committed rules needs no API key: `uv run pytest`, or run the gates
the way CI does with `semgrep --config rules/<id>.yaml incidents/<id>/bad.py`.

## Worked example

`incidents/001-jwt-in-logs/` describes a bearer token written into a logger
call. `bad.py` logs `f"...token={token}"`; `good.py` logs a static string. The
compiler drafts a rule, runs it against both files, and only writes
`rules/001-jwt-in-logs.yaml` once it produces a finding on `bad.py` and none on
`good.py`. If the first draft over- or under-matches, the gate error is fed back
into the prompt and it retries, up to three times.

## Limitations (v0.1)

- Python only.
- `pattern` / `pattern-either` style rules. No taint mode.
- No autofix generation.
- CLI only — no SaaS, API, or UI.
- Direct Anthropic SDK call. No model abstraction layer.
- Semgrep is a Linux/macOS tool; on Windows run the compiler under WSL, Docker,
  or in CI.

## Roadmap

- Real incidents from production experience, replacing the three seeds.
- More languages once the Python loop is proven.
- Taint-mode rules for dataflow incidents.
- Autofix suggestions, gated the same way.

## License

Apache 2.0. See [LICENSE](LICENSE).
