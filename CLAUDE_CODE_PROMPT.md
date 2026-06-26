# Claude Code prompt — scaffold semgrep-rule-compiler

Paste the block below into a fresh Claude Code session opened at `C:\Users\boris\IntentArch\vault\compilied-ai-github\semgrep-rule-compiler`.

Before pasting, drop these files in place:

- `PLAN.md` at repo root
- `CLAUDE.md` at repo root (from the template, with the placeholders filled in for this repo)
- `.claude/commands/*.md` (the four slash commands from the template)

---

```
Read PLAN.md. Read CLAUDE.md. Scaffold the repo accordingly.

What to do:
- Create the full directory layout from PLAN.md.
- Implement src/srcompile/{cli.py, compiler.py, validator.py} per the compile loop in PLAN.md.
- Write the prompt template at src/srcompile/prompts/rule_from_incident.md.
- Write pyproject.toml for uv, Python 3.11+, with anthropic, pyyaml, and click as runtime deps; pytest and ruff as dev deps.
- Create the three seed incident folders (incidents/001-jwt-in-logs, 002-sql-fstring, 003-requests-no-timeout). Each gets a realistic incident.md (3-6 lines), a bad.py that exhibits the pattern, and a good.py that fixes it. Keep them under 20 lines each.
- Leave rules/ empty with a .gitkeep. The compiler produces those.
- Write tests/test_validator.py covering the four gates with one passing and one failing fixture per gate.
- Write .github/workflows/verify.yml. It installs semgrep, then runs every rules/*.yaml against the matching incidents/*/bad.py (must flag) and incidents/*/good.py (must not flag). Skip cleanly if rules/ is empty.
- Write .github/workflows/compile.yml as a manual-dispatch workflow that runs srcompile, opens a PR with the regenerated rules/. Do not auto-merge.
- Write README.md per the structure in PLAN.md's distribution section: one-paragraph what, one-paragraph why with a Medium-article placeholder link, the five-part flow, three-command try-it, worked example pointing at 001, limitations, roadmap.
- Add LICENSE — full Apache 2.0 text, copyright "Boris Teplitsky".

What NOT to do:
- Do not run the compiler. Do not call any LLM. Just scaffold so it is ready to run.
- Do not generate the rules/*.yaml files. Those come from running srcompile against incidents/.
- Do not add a model abstraction layer, retry library, or observability framework. Direct anthropic SDK call, three-attempt retry implemented inline.
- Do not add marketing language anywhere. No emojis. No "Built with ❤". Sentence case in all docs.

Voice: terse, technical. My usual.

When done: list every file you created, then stop. I will review before any commit.
```

---

After Claude Code finishes, verify manually:

1. `tree` shows the layout matches PLAN.md exactly.
2. `uv sync` resolves without errors.
3. `uv run pytest` passes.
4. `uv run srcompile --help` shows the CLI.
5. The three `incidents/*/bad.py` files each exhibit a real pattern you would actually flag.

Then set `ANTHROPIC_API_KEY` and run `uv run srcompile build ./incidents` to produce the first round of `rules/*.yaml`. Review each rule by eye before committing.
