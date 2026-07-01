"""srcompile command line.

`srcompile build ./specs` compiles every spec into a rule under rules/. Exit
code is non-zero if any spec failed its gates, so CI and the compile workflow
can tell a partial run from a clean one. Specs the model declares UNEXPRESSIBLE
are reported as skipped and do not fail the run.
"""
from __future__ import annotations

import sys
from pathlib import Path

import click

from srcompile.compiler import compile_all


@click.group()
def main() -> None:
    """Compile prose specs into gate-verified Semgrep rules."""


@main.command()
@click.argument(
    "spec_dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--rules-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("rules"),
    show_default=True,
    help="Where compiled rules are written.",
)
def build(spec_dir: Path, rules_dir: Path) -> None:
    """Compile every spec in SPEC_DIR into a rule."""
    results = compile_all(spec_dir, rules_dir)

    failed = [r for r in results if r.status == "failed"]
    skipped = [r for r in results if r.status == "skipped"]
    compiled = [r for r in results if r.status == "compiled"]

    for r in results:
        if r.status == "compiled":
            click.echo(f"  compiled  {r.spec_id}  ({r.attempts} attempt(s))")
        elif r.status == "skipped":
            click.echo(f"  skipped   {r.spec_id}  (unexpressible: {r.detail})")
        else:
            click.echo(f"  FAILED    {r.spec_id}  after {r.attempts} attempts")
            if r.detail:
                click.echo(_indent(r.detail))

    click.echo()
    click.echo(
        f"{len(compiled)}/{len(results)} compiled, "
        f"{len(skipped)} skipped, {len(failed)} failed."
    )
    if failed:
        click.echo(
            f"{len(failed)} spec(s) failed gates; no rule written for those."
        )
        sys.exit(1)


def _indent(text: str, prefix: str = "            ") -> str:
    return "\n".join(prefix + line for line in text.splitlines())


if __name__ == "__main__":
    main()
