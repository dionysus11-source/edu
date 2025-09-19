#!/usr/bin/env python3
"""Plot per-epoch evaluation metrics recorded during training."""
import argparse
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_METRICS = [
    "eval_accuracy",
    "eval_precision",
    "eval_recall",
    "eval_f1",
    "eval_normal_recall",
    "eval_defect_recall",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize evaluation metrics across epochs.")
    parser.add_argument(
        "--metrics-file",
        default="logs/metrics_history.csv",
        help="Path to the CSV produced by MetricsCSVLogger (default: logs/metrics_history.csv).",
    )
    parser.add_argument(
        "--metrics",
        nargs="*",
        default=DEFAULT_METRICS,
        help="Specific metric columns to plot (default: accuracy, precision, recall, f1, normal/defect recall).",
    )
    parser.add_argument(
        "--output",
        help="Optional path to save the figure. If omitted, the plot window is shown interactively.",
    )
    parser.add_argument(
        "--title",
        default="Evaluation Metrics by Epoch",
        help="Title for the generated chart.",
    )
    return parser.parse_args()


def filter_metrics(columns: List[str], available: List[str]) -> List[str]:
    filtered = [col for col in columns if col in available]
    missing = sorted(set(columns) - set(filtered))
    if missing:
        print(f"⚠️  Skipping missing metrics: {', '.join(missing)}")
    return filtered


def main() -> None:
    args = parse_args()
    csv_path = Path(args.metrics_file)
    if not csv_path.exists():
        raise FileNotFoundError(f"Metrics CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if "epoch" not in df.columns:
        raise ValueError("CSV must include an 'epoch' column recorded by MetricsCSVLogger.")

    metrics = filter_metrics(args.metrics, df.columns.tolist())
    if not metrics:
        raise ValueError("No valid metrics to plot. Verify the CSV contents or adjust --metrics.")

    df = df.sort_values("epoch")

    plt.figure(figsize=(10, 6))
    for metric in metrics:
        plt.plot(df["epoch"], df[metric], marker="o", label=metric)

    plt.title(args.title)
    plt.xlabel("Epoch")
    plt.ylabel("Metric Value")
    plt.grid(True, alpha=0.3)
    plt.legend()

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, bbox_inches="tight")
        print(f"✅ Plot saved to {output_path}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
