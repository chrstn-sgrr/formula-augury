"""Command line entry point: `uv run python -m formula_augury build ...`."""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="formula-augury")
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="fetch one race and write the processed dataset")
    build.add_argument("--season", type=int, required=True)
    build.add_argument("--round", type=int, required=True)
    build.add_argument("--cache-dir", type=Path, default=REPO_ROOT / ".fastf1cache")
    build.add_argument("--out-dir", type=Path, default=REPO_ROOT / "data" / "processed")

    args = parser.parse_args(argv)

    from .dataset import IneligibleEvent, build_dataset, write_dataset
    from .source import SourceUnavailable, load_event

    try:
        event = load_event(args.season, args.round, args.cache_dir)
        stints, results = build_dataset(event)
    except SourceUnavailable as error:
        print(f"source unavailable: {error}", file=sys.stderr)
        return 2
    except IneligibleEvent as error:
        print(f"ineligible event: {error}", file=sys.stderr)
        return 3

    import fastf1

    paths = write_dataset(stints, results, args.out_dir, event, f"fastf1 {fastf1.__version__}")
    print(f"{event.meta.season} round {event.meta.round}: {event.meta.name}")
    print(f"{len(stints)} stint rows, {len(results)} result rows")
    for label, path in paths.items():
        print(f"{label}: {path}")
    return 0
