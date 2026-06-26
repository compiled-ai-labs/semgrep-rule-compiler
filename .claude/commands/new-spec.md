Scaffold a new spec entry in this compiled-ai repo.

Name: $ARGUMENTS

Steps:

1. Read CLAUDE.md and PLAN.md to determine:
   - The spec folder name (e.g. `incidents/`, `policies/`, `specs/`)
   - The expected file set per entry (e.g. `incident.md`, `bad.py`, `good.py`)
2. Find the highest existing numeric prefix in the spec folder. New entry uses next number, three digits, kebab-case suffix from $ARGUMENTS.
3. Create the subfolder and the standard files with empty stubs and a one-line comment in each explaining what content goes there.
4. Do not invoke the compiler. Do not write to the artifact folder.
5. Print the path of the new folder and list the stub files. Stop.

If $ARGUMENTS is empty, ask for the spec name and stop.
