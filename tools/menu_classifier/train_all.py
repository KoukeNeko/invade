#!/usr/bin/env python3
"""
Batch trainer that scans the data directory and trains all vocab classifiers.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Tuple

import build_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train classifiers for all context corpora.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).parent / "data",
        help="Directory containing *_contexts.jsonl corpora.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        help="Optional list of targets (basename without _contexts.jsonl) to train.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Override output path for all classifiers (defaults to build_model setting or dataset meta).",
    )
    parser.add_argument(
        "--ignore-meta",
        action="store_true",
        help="Ignore dataset meta overrides embedded in JSONL files.",
    )
    return parser.parse_args()


def iter_datasets(data_dir: Path) -> Iterable[Tuple[str, Path]]:
    pattern = "*_contexts.jsonl"
    for path in sorted(data_dir.glob(pattern)):
        stem = path.stem
        if stem.endswith("_contexts"):
            target = stem[: -len("_contexts")]
        else:
            target = stem
        yield target, path


def run_batch(args: argparse.Namespace) -> int:
    if not args.data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {args.data_dir}")

    defaults_ns = build_model.build_arg_parser().parse_args([])
    defaults = vars(defaults_ns)
    exit_code = 0

    selected = set(args.only or [])
    processed = False

    for target, dataset in iter_datasets(args.data_dir):
        if selected and target not in selected:
            continue

        processed = True
        values = defaults.copy()
        values["input"] = dataset
        if args.output is not None:
            values["output"] = args.output

        namespace = argparse.Namespace(**values)
        status = build_model.train_from_args(namespace, defaults=defaults_ns, allow_meta=not args.ignore_meta)
        if status != 0:
            exit_code = status

    if not processed:
        print("No datasets matched the provided filters.", file=sys.stderr)
        return 1
    return exit_code


def main() -> int:
    args = parse_args()
    try:
        return run_batch(args)
    except Exception as exc:  # noqa: BLE001
        print(f"Batch training failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
