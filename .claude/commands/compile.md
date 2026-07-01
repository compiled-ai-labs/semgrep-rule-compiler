Run the compiler for this compiled-ai repo.

Steps:

1. Verify `ANTHROPIC_API_KEY` is set in the environment. If not, stop and tell the user.
2. Read CLAUDE.md to find the compile entry point (e.g. `uv run srcompile build ./specs`).
3. Run the entry point. Stream output.
4. After it finishes, report per spec entry:
   - Compiled cleanly (artifact written)
   - Failed gates after 3 retries (no artifact written, error shown)
5. Do not commit the artifacts. Run `git status` and `git diff` on the artifact folder. Show the diff to the user and stop.

The user reviews and commits manually.
