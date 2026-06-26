Run validation gates on every committed artifact in this compiled-ai repo.

This is the regression check. It detects when a spec was edited but the artifact was not recompiled, or when an external tool version changed.

Steps:

1. Read CLAUDE.md to find:
   - The spec folder
   - The artifact folder
   - The runtime tool (e.g. semgrep, conftest, terraform)
2. For each artifact in the artifact folder, locate the matching spec entry (by numeric prefix or shared name).
3. Run the runtime tool against the spec's known-failing input — must produce the expected verdict.
4. Run the runtime tool against the spec's known-passing input — must NOT produce the verdict.
5. Print a table: artifact id, gate result (pass / fail), short error if fail.
6. Exit non-zero if any artifact fails. This matches what CI does in `verify.yml`.

Do not invoke the LLM. Do not regenerate artifacts. This command never writes.
