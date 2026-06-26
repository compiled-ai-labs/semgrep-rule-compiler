# CLAUDE.md

This repo follows the **Compiled AI** paradigm. The LLM runs at compile time to produce a deterministic artifact. The runtime tool consumes that artifact without any model in the path.

See the `compiled-ai` skill for the full paradigm and conventions. If the skill is not loaded, treat this file as the authoritative reference.

## This repo

- **One-liner:** Compile postmortems and code samples into Semgrep rules.
- **Spec folder:** `incidents/`
- **Compiler entry:** `uv run srcompile build ./incidents`
- **Artifact folder:** `rules/`
- **Runtime tool:** `semgrep`

## The pattern (always)

1. **Spec** — markdown plus minimal worked examples (bad/good pairs, sample inputs). Source of truth. Human-maintained.
2. **Compiler** — `src/<package>/compiler.py`. Calls LLM with a templated prompt. Runs offline.
3. **Validation gates** — `src/<package>/validator.py`. Non-negotiable. Parse, lint, functional verdict on known cases.
4. **Artifact** — committed file. Reviewable like any code. Versioned. Pinned by consumers.
5. **Runtime** — boring deterministic tool. Consumes the artifact. No LLM.

## Validation discipline

The LLM does not get its output committed unless an external validator agrees the artifact does what it claims. No exceptions.

- Parse first. If it does not parse, retry with the parse error fed back into the prompt.
- Then run against known-failing input. The artifact MUST produce the expected verdict.
- Then run against known-passing input. The artifact MUST NOT produce the verdict.
- Maximum 3 retries with feedback. After that, surface to human and write nothing.

## What this repo is NOT

This repo does not contain runtime AI. There is no LLM call in any code path triggered by user actions or scanner runs. If a contributor proposes one, push back and point them at the Compiled AI thesis.

## Voice and style

- Terse, technical. No marketing language. No AI markers. No emoji.
- Sentence case in all docs and commit messages.
- Pushback expected when responses over-explain or drift from the actual question.

## Workflow commands

- `/new-spec <name>` — scaffold a new spec entry in the spec folder.
- `/compile` — run the compile loop locally.
- `/verify` — run gates on all existing committed artifacts.
- `/check-pattern` — audit this repo for drift from the five-part shape.

## Locked decisions (Compiled AI Labs default)

- License: Apache 2.0.
- LLM: Anthropic SDK direct. Model configurable via `<PACKAGE>_MODEL` env var.
- Python: 3.11+, uv for package management.
- Tests: pytest. Lint: ruff.
- CI: GitHub Actions. Two workflows: `compile.yml` (manual dispatch, opens PR with regenerated artifacts) and `verify.yml` (every PR, runs gates on committed artifacts).
