Audit this repo for drift from the Compiled AI paradigm.

The paradigm has five parts and one prohibition. Check each.

The five parts must exist:

1. **Spec folder** — human-maintained, contains worked examples (bad/good pairs or equivalent).
2. **Compiler** — script that calls an LLM. Lives in `src/` or equivalent.
3. **Validation gates** — automated checks the artifact must pass before commit. At minimum: parse check, functional verdict on known cases.
4. **Artifact folder** — committed files, reviewable as code.
5. **Runtime invocation** — documented in README. Uses a deterministic tool. No LLM in this path.

The prohibition:

- No LLM call in any code path triggered by a scanner run, a CI job on user code, a webhook, or a user request. The LLM only runs when the maintainer triggers the compiler.

Steps:

1. Locate each of the five parts. Report which are present and which are missing.
2. Grep the runtime path (anything imported by CI workflows other than the compile workflow) for LLM SDK imports (`anthropic`, `openai`, `litellm`, `langchain`, etc.). Report any hits as critical drift.
3. Check README documents the runtime usage clearly. If the runtime tool is not named, flag it.
4. Check CLAUDE.md exists and is filled in (no `<!-- FILL IN -->` placeholders left).
5. Print a summary: PASS / DRIFT, with specific findings.

Do not modify any files. This is a read-only audit.
