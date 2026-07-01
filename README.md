# semgrep-rule-compiler

Compile prose coding standards and incident writeups into Semgrep rules. An LLM
runs at compile time to turn each spec — a free-text `source.md` plus a
`bad.py`/`good.py` fixture pair — into Semgrep YAML. The scanner runs at runtime
with no model in the path. A rule is only written when Semgrep itself confirms it
flags the bad fixture and passes the good.

## Why

LLMs are good at drafting a Semgrep rule from an example and bad at being
trusted with it. The usual answer — paste code into a chat, copy the rule out,
hope — has no check that the rule does what it claims. This repo puts the model
behind a gate: the rule is generated offline, validated against the exact bad
and good samples it was built from, and committed as a plain file. The thing you
run in CI is Semgrep, deterministic and auditable, not a model. The input is
authoritative prose — a coding standard or an incident record — exactly the kind
of stable, human-written source that cannot be parsed deterministically and must
not be evaluated by a model at runtime; it is read once, at compile time, into a
rule that outlives it. Background:
["Compiled AI: Engineering Deterministic LLM Systems"](https://medium.com/@boristeplitsky)
(placeholder link).

## The five-part flow

1. **Spec** — `specs/<id>/` with `source.md` (prose, primary), plus `bad.py`, `good.py` fixtures. Human-maintained.
2. **Compiler** — `src/srcompile/compiler.py`. Calls Anthropic with a templated prompt. Offline.
3. **Validation gates** — `src/srcompile/validator.py`. Parse, `semgrep --validate`, flag bad, pass good.
4. **Artifact** — `rules/<id>.yaml`. Committed, reviewable, pinned by consumers.
5. **Runtime** — `semgrep`. Deterministic. No LLM in this path.

## Try it

```bash
uv sync
export ANTHROPIC_API_KEY=sk-...
uv run srcompile build ./specs
```

This writes one `rules/<id>.yaml` per spec that passes all four gates, and exits
non-zero if any spec fails. Review each rule against its `source.md`, not just the
fixtures — the point is that the rule generalises from the prose. Verifying
committed rules needs no API key: `uv run pytest`, or run the gates the way CI
does with `semgrep --config rules/<id>.yaml specs/<id>/bad.py`.

## Worked example

`specs/001-secrets-in-logs/source.md` is a coding-guide excerpt: no secret or
personal identifier is ever passed to a logging call, in the message or in any
argument. The fixtures pin two edges — `bad.py` logs `f"...token={token}"`,
`good.py` logs a static string. The compiler reads the prose as the specification,
drafts a rule meant to enforce that general principle, and only writes
`rules/001-secrets-in-logs.yaml` once the rule produces a finding on `bad.py` and
none on `good.py`. If a draft over- or under-matches, the gate error is fed back
into the prompt and it retries, up to three times. The fixtures gate the rule; the
prose is what it must actually capture.

## Limitations (v0.1)

- Python only.
- `pattern` / `pattern-either` style rules. No taint mode.
- No autofix generation.
- CLI only — no SaaS, API, or UI.
- Direct Anthropic SDK call. No model abstraction layer.
- Fixtures are not held out — the model sees `bad.py`/`good.py` while writing the
  rule, so it can overfit those two points and still pass the gates. Nothing
  automatically checks that the rule captures the prose's full generality; human
  review of rule-against-`source.md` is expected on every compile.
- If a spec's principle cannot be expressed as a Semgrep pattern, the compiler
  reports it as `UNEXPRESSIBLE` and writes no rule, rather than forcing a bad one.
- Semgrep is a Linux/macOS tool; on Windows run the compiler under WSL, Docker,
  or in CI.

## Roadmap

- Real coding standards and incidents from production experience, replacing the three seeds.
- More languages once the Python loop is proven.
- Taint-mode rules for dataflow incidents.
- Autofix suggestions, gated the same way.

## Related work

- **Autogrep** — LLM plus a multi-stage filtering pipeline that turns vulnerability
  patches into Semgrep rules across 20 languages. It mines rules in bulk from public
  patches and filters out the overly specific ones; this compiles one rule per
  human-written spec — a prose coding standard or incident writeup — and
  gate-verifies it against that spec's bad/good fixtures before commit.
- **RuleLLM** (arXiv:2504.17198) — generates YARA and Semgrep rules from
  malicious-package metadata, with refine and align stages and an agent to curb
  hallucination. It self-checks with more model calls; this defers the check to
  Semgrep itself running on known samples.
- **SemOpt** (arXiv:2510.16384) — an LLM agent that derives a Semgrep rule from a
  commit's optimization strategy and retries until the rule executes. Its loop gates
  on "the rule runs," not on "the rule fires on the bad case and stays silent on the
  good one."
- **semgrep/semgrep-rules** — the curated community ruleset, hand-maintained by
  Semgrep and contributors. A fixed expert catalog; this compiles rules from your
  own coding standards and incidents instead of shipping a registry.
- **Semgrep Assistant** — Semgrep's in-platform AI for suggesting rules and triaging
  findings. Runtime, SaaS-coupled assistance; this keeps the model offline at compile
  time and leaves no inference in the scan path.

## Collaborate

This is the first reference implementation of the Compiled AI paradigm — an
LLM authors deterministic artifacts at compile time, runtime stays free of
inference. The same shape fits OPA policies, Terraform modules, GitHub
Actions workflows, CODEOWNERS, Dependabot configs, and more.

Three ways to get involved:

- **Use it.** Open an issue with a rule pattern you'd want compiled, or
  drop a postmortem snippet you'd turn into a Semgrep rule.
- **Extend it.** PRs for new languages (Go, JS/TS), taint-mode rules, or
  autofix suggestions — all gated the same way.
- **Build the next compiler.** If you have a deterministic tool that
  consumes config or rules (OPA, Terraform, GitHub Actions, an in-house
  policy engine), open an issue describing the use case. I'm actively
  building out the `compiled-ai-labs` org and looking for collaborators
  on adjacent compile targets.

Contact: open an issue here, or `compiledailabs@gmail.com`.

## License

Apache 2.0. See [LICENSE](LICENSE).
