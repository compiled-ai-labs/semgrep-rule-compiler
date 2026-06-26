"""srcompile command line.

`srcompile build ./incidents` compiles every incident into a rule under rules/.
Exit code is non-zero if any incident failed its gates, so CI and the compile
workflow can tell a partial run from a clean one.
"""
from __future__ import annotations

import sys
from pathlib import Path

import click

from srcompile.compiler import compile_all


@click.group()
def main() -> None:
    """Compile incidents into gate-verified Semgrep rules."""


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
    """Compile every incident in SPEC_DIR into a rule."""
    results = compile_all(spec_dir, rules_dir)

    failed = [r for r in results if not r.compiled]
    for r in results:
        if r.compiled:
            click.echo(f"  compiled  {r.incident_id}  ({r.attempts} attempt(s))")
        else:
            click.echo(f"  FAILED    {r.incident_id}  after {r.attempts} attempts")
            if r.failure:
                click.echo(_indent(r.failure))

    click.echo()
    click.echo(f"{len(results) - len(failed)}/{len(results)} incident(s) compiled.")
    if failed:
        click.echo(
            f"{len(failed)} incident(s) failed gates; no rule written for those."
        )
        sys.exit(1)


def _indent(text: str, prefix: str = "            ") -> str:
    return "\n".join(prefix + line for line in text.splitlines())


if __name__ == "__main__":
    main()
