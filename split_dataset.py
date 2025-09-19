"""Create train/eval splits for the code defect dataset pipeline.

Reads one or more JSONL sources (by default `enhanced_boxing_dataset.jsonl`
and `singleton.jsonl`), performs a stratified split on `has_defect`, and saves
the results as Hugging Face datasets under `train_dataset/` and `test_dataset/`.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Iterable, List

import pandas as pd
from datasets import Dataset, concatenate_datasets, ClassLabel


DEFAULT_SOURCES: List[Path] = [
    Path("enhanced_boxing_dataset.jsonl"),
    Path("singleton.jsonl"),
]


def load_jsonl_dataset(path: Path) -> Dataset:
    if not path.exists():
        raise FileNotFoundError(f"Dataset source not found: {path}")

    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))

    if not rows:
        raise ValueError(f"Dataset source {path} is empty")

    return Dataset.from_pandas(pd.DataFrame(rows), preserve_index=False)
def load_sources(sources: Iterable[Path]) -> List[Dataset]:
    datasets = [load_jsonl_dataset(Path(src)) for src in sources]
    if not datasets:
        raise ValueError("No valid datasets loaded; check source paths")
    return datasets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split datasets for training/evaluation")
    parser.add_argument(
        "--source",
        action="append",
        type=Path,
        help="Additional JSONL dataset source (can be repeated). Defaults are enhanced_boxing_dataset.jsonl and singleton.jsonl.",
    )
    parser.add_argument("--train-dir", type=Path, default=Path("train_dataset"))
    parser.add_argument("--eval-dir", type=Path, default=Path("test_dataset"))
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    sources = args.source if args.source else DEFAULT_SOURCES

    datasets = load_sources(sources)

    if not 0.0 < args.test_size < 1.0:
        raise ValueError("--test-size must be between 0 and 1")

    train_parts: List[Dataset] = []
    eval_parts: List[Dataset] = []

    for dataset in datasets:
        if "has_defect" not in dataset.column_names:
            raise ValueError("Each dataset must contain a 'has_defect' column")

        feature = dataset.features.get("has_defect")
        if not isinstance(feature, ClassLabel):
            dataset = dataset.cast_column(
                "has_defect",
                ClassLabel(names=["normal", "defect"]),
            )

        split = dataset.train_test_split(
            test_size=args.test_size,
            seed=args.seed,
            stratify_by_column="has_defect",
        )
        train_parts.append(split["train"])
        eval_parts.append(split["test"])

    train_dataset = (
        concatenate_datasets(train_parts) if len(train_parts) > 1 else train_parts[0]
    )
    eval_dataset = (
        concatenate_datasets(eval_parts) if len(eval_parts) > 1 else eval_parts[0]
    )

    if args.train_dir.exists():
        shutil.rmtree(args.train_dir)
    if args.eval_dir.exists():
        shutil.rmtree(args.eval_dir)

    train_dataset.save_to_disk(str(args.train_dir))
    eval_dataset.save_to_disk(str(args.eval_dir))

    print(f"Train dataset saved to {args.train_dir}")
    print(f"Eval dataset saved to {args.eval_dir}")


if __name__ == "__main__":
    main()
