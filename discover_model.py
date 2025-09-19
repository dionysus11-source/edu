"""Benchmark multiple transformer models for defect code classification.

This script trains a lightweight classifier for each configured Hugging Face
checkpoint on the enhanced boxing dataset, captures quality metrics and
resource measurements, and renders comparison charts to support model
selection.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import matplotlib


matplotlib.use("Agg")  # headless environments

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from datasets import Dataset, load_from_disk
from sklearn.metrics import classification_report
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
    set_seed,
)


LABEL_NAMES = {0: "normal", 1: "defect"}


@dataclass
class ModelSpec:
    """Holds model metadata for comparisons."""

    display_name: str
    hf_id: str
    family: str


MODEL_SPECS: List[ModelSpec] = [
    ModelSpec("CodeBERT", "microsoft/codebert-base", "code-specific"),
    ModelSpec("GraphCodeBERT", "microsoft/graphcodebert-base", "code-specific"),
    ModelSpec("CodeBERTa-small", "huggingface/CodeBERTa-small-v1", "code-specific"),
    ModelSpec("RoBERTa-base", "roberta-base", "general-purpose"),
    ModelSpec("DistilRoBERTa", "distilroberta-base", "general-purpose"),
]


def load_boxing_dataset(path: Path) -> Dataset:
    """Load the boxing dataset JSONL file into a Hugging Face Dataset."""

    texts: List[str] = []
    labels: List[int] = []
    defect_types: List[int] = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            texts.append(row["text"])
            labels.append(int(row["has_defect"]))
            defect_types.append(int(row.get("defect_type", 0)))

    dataset = Dataset.from_dict({
        "text": texts,
        "labels": labels,
        "defect_type": defect_types,
    })

    return dataset


def compute_metrics(eval_pred) -> Dict[str, float]:
    """Compute weighted metrics and per-class statistics."""

    predictions, labels = eval_pred
    predicted_labels = predictions.argmax(axis=-1)

    report = classification_report(
        labels,
        predicted_labels,
        labels=list(LABEL_NAMES.keys()),
        target_names=list(LABEL_NAMES.values()),
        output_dict=True,
        zero_division=0,
    )

    weighted = report.get("weighted avg", {})

    metrics = {
        "accuracy": report.get("accuracy", 0.0),
        "precision": weighted.get("precision", 0.0),
        "recall": weighted.get("recall", 0.0),
        "f1": weighted.get("f1-score", 0.0),
    }

    for label_name, stats in report.items():
        if label_name in ("accuracy", "macro avg", "weighted avg"):
            continue
        metrics[f"{label_name}_precision"] = stats.get("precision", 0.0)
        metrics[f"{label_name}_recall"] = stats.get("recall", 0.0)
        metrics[f"{label_name}_f1"] = stats.get("f1-score", 0.0)
        metrics[f"{label_name}_support"] = stats.get("support", 0)

    return metrics


def prepare_datasets(
    train_dataset: Dataset,
    eval_dataset: Dataset,
    tokenizer,
    max_length: int,
    max_train_samples: Optional[int] = None,
    max_eval_samples: Optional[int] = None,
):
    """Tokenize datasets with model-specific tokenizer."""

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            padding=False,
            max_length=max_length,
        )

    remove_columns = [col for col in train_dataset.column_names if col != "labels"]

    mapped_train = train_dataset
    mapped_eval = eval_dataset

    if max_train_samples:
        mapped_train = mapped_train.select(range(min(max_train_samples, len(mapped_train))))
    if max_eval_samples:
        mapped_eval = mapped_eval.select(range(min(max_eval_samples, len(mapped_eval))))

    tokenized_train = mapped_train.map(
        tokenize,
        batched=True,
        remove_columns=remove_columns,
    )
    tokenized_eval = mapped_eval.map(
        tokenize,
        batched=True,
        remove_columns=remove_columns,
    )

    return tokenized_train, tokenized_eval


def benchmark_model(
    spec: ModelSpec,
    train_dataset: Dataset,
    eval_dataset: Dataset,
    test_dataset: Optional[Dataset],
    args: argparse.Namespace,
    output_dir: Path,
):
    """Train and evaluate a single model, returning collected metrics."""

    print(f"\n=== Benchmarking {spec.display_name} ({spec.hf_id}) ===")

    tokenizer = AutoTokenizer.from_pretrained(spec.hf_id, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        spec.hf_id,
        num_labels=len(LABEL_NAMES),
        problem_type="single_label_classification",
    )

    tokenized_train, tokenized_eval = prepare_datasets(
        train_dataset,
        eval_dataset,
        tokenizer,
        max_length=args.max_length,
        max_train_samples=args.max_train_samples,
        max_eval_samples=args.max_eval_samples,
    )

    if test_dataset is not None:
        tokenized_test, _ = prepare_datasets(
            test_dataset,
            test_dataset,
            tokenizer,
            max_length=args.max_length,
            max_train_samples=args.max_test_samples,
            max_eval_samples=args.max_test_samples,
        )
    else:
        tokenized_test = None

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    model_output_dir = output_dir / f"{spec.display_name.replace(' ', '_').lower()}"
    model_output_dir.mkdir(parents=True, exist_ok=True)

    init_params = TrainingArguments.__init__.__code__.co_varnames

    training_args_kwargs = dict(
        output_dir=str(model_output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.train_batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        seed=args.seed,
    )

    if "logging_strategy" in init_params:
        training_args_kwargs["logging_strategy"] = "steps"
    if "logging_steps" in init_params:
        training_args_kwargs["logging_steps"] = args.logging_steps
    if "report_to" in init_params:
        training_args_kwargs["report_to"] = "none"
    if "save_strategy" in init_params:
        training_args_kwargs["save_strategy"] = "no"

    # Older Transformers (<4.10) expect eval_strategy instead of evaluation_strategy.
    if "eval_strategy" in init_params:
        training_args_kwargs["eval_strategy"] = "epoch"
    elif "evaluation_strategy" in init_params:
        training_args_kwargs["evaluation_strategy"] = "epoch"

    training_args = TrainingArguments(**training_args_kwargs)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_eval,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    result: Dict[str, float] = {
        "model": spec.display_name,
        "hf_id": spec.hf_id,
        "family": spec.family,
        "status": "ok",
        "params_million": float(model.num_parameters() / 1e6),
        "train_samples": len(tokenized_train),
        "eval_samples": len(tokenized_eval),
        "test_samples": len(tokenized_test) if tokenized_test is not None else 0,
    }

    try:
        start_train = time.perf_counter()
        train_output = trainer.train()
        train_runtime = time.perf_counter() - start_train
        result["train_runtime_sec"] = train_runtime
        result["train_samples_per_second"] = train_output.metrics.get(
            "train_samples_per_second", 0.0
        )
        result["epoch"] = train_output.metrics.get("epoch", args.epochs)

        start_eval = time.perf_counter()
        eval_metrics = trainer.evaluate()
        eval_runtime = time.perf_counter() - start_eval
        result["eval_runtime_sec"] = eval_runtime

        for key, value in eval_metrics.items():
            result[key] = float(value)

        prediction = trainer.predict(tokenized_eval)
        for key, value in prediction.metrics.items():
            result[f"pred_{key}"] = float(value)

        if tokenized_test is not None:
            test_prediction = trainer.predict(tokenized_test)
            for key, value in test_prediction.metrics.items():
                result[f"test_{key}"] = float(value)
            # reuse compute_metrics for test set labels/preds
            test_metrics = compute_metrics(
                (test_prediction.predictions, tokenized_test["labels"])
            )
            for key, value in test_metrics.items():
                result[f"test_{key}"] = float(value)

    except Exception as exc:  # pragma: no cover - defensive path
        result["status"] = "failed"
        result["error"] = str(exc)
        print(f"Model {spec.display_name} failed: {exc}")

    return result


def plot_metrics(df: pd.DataFrame, output_dir: Path) -> None:
    """Render comparison charts from the collected results."""

    ok_df = df[df["status"] == "ok"].copy()
    if ok_df.empty:
        print("No successful models to plot.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    metric_cols = [
        col
        for col in ["eval_accuracy", "eval_precision", "eval_recall", "eval_f1"]
        if col in ok_df.columns
    ]

    if metric_cols:
        melted = ok_df.melt(
            id_vars=["model", "family"],
            value_vars=metric_cols,
            var_name="metric",
            value_name="value",
        )
        plt.figure(figsize=(10, 6))
        sns.barplot(
            data=melted,
            x="model",
            y="value",
            hue="metric",
            palette="viridis",
        )
        plt.ylim(0.0, 1.05)
        plt.title("Evaluation Metrics by Model")
        plt.ylabel("Score")
        plt.xlabel("Model")
        plt.legend(title="Metric")
        plt.xticks(rotation=15)
        plt.tight_layout()
        plt.savefig(output_dir / "metrics_comparison.png")
        plt.close()

    if {"train_runtime_sec", "eval_runtime_sec"}.issubset(ok_df.columns):
        runtime_df = ok_df.melt(
            id_vars=["model"],
            value_vars=["train_runtime_sec", "eval_runtime_sec"],
            var_name="phase",
            value_name="seconds",
        )
        plt.figure(figsize=(10, 6))
        sns.barplot(
            data=runtime_df,
            x="model",
            y="seconds",
            hue="phase",
            palette="magma",
        )
        plt.title("Runtime by Model")
        plt.ylabel("Seconds")
        plt.xlabel("Model")
        plt.xticks(rotation=15)
        plt.tight_layout()
        plt.savefig(output_dir / "runtime_comparison.png")
        plt.close()

    if {"params_million", "eval_f1"}.issubset(ok_df.columns):
        plt.figure(figsize=(8, 6))
        sns.scatterplot(
            data=ok_df,
            x="params_million",
            y="eval_f1",
            hue="family",
            style="model",
            s=160,
        )
        plt.title("Model Size vs. F1")
        plt.xlabel("Parameters (millions)")
        plt.ylabel("Eval F1")
        for _, row in ok_df.iterrows():
            plt.text(
                row["params_million"] + 0.5,
                row["eval_f1"],
                row["model"],
                fontsize=9,
            )
        plt.tight_layout()
        plt.savefig(output_dir / "size_vs_f1.png")
        plt.close()

    if {"pred_test_samples_per_second", "eval_f1"}.issubset(ok_df.columns):
        plt.figure(figsize=(8, 6))
        sns.scatterplot(
            data=ok_df,
            x="pred_test_samples_per_second",
            y="eval_f1",
            hue="model",
            s=160,
        )
        plt.title("Throughput vs. F1 (Validation)")
        plt.xlabel("Eval Samples per Second")
        plt.ylabel("Eval F1")
        plt.tight_layout()
        plt.savefig(output_dir / "throughput_vs_f1.png")
        plt.close()


def load_test_dataset(path: Path) -> Optional[Dataset]:
    """Load the persisted test dataset if available."""

    if not path.exists():
        return None

    dataset = load_from_disk(str(path))
    drop_cols = [
        col
        for col in dataset.column_names
        if col not in {"text", "labels", "defect_type"}
    ]
    if drop_cols:
        dataset = dataset.remove_columns(drop_cols)
    return dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark multiple transformer models")
    parser.add_argument("--data", type=Path, default=Path("enhanced_boxing_dataset.jsonl"))
    parser.add_argument("--test-dataset", type=Path, default=Path("test_dataset"))
    parser.add_argument("--output-dir", type=Path, default=Path("discover_model_outputs"))
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--learning-rate", dest="learning_rate", type=float, default=2e-5)
    parser.add_argument("--weight-decay", dest="weight_decay", type=float, default=0.01)
    parser.add_argument("--train-batch-size", dest="train_batch_size", type=int, default=4)
    parser.add_argument("--eval-batch-size", dest="eval_batch_size", type=int, default=4)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=1)
    parser.add_argument("--logging-steps", type=int, default=50)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--max-train-samples", dest="max_train_samples", type=int)
    parser.add_argument("--max-eval-samples", dest="max_eval_samples", type=int)
    parser.add_argument("--max-test-samples", dest="max_test_samples", type=int)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    dataset = load_boxing_dataset(args.data)
    dataset = dataset.remove_columns([col for col in dataset.column_names if col == "defect_type"])

    split = dataset.train_test_split(test_size=0.2, seed=args.seed)
    train_dataset = split["train"]
    eval_dataset = split["test"]

    test_dataset = load_test_dataset(args.test_dataset)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    results: List[Dict[str, float]] = []

    for spec in MODEL_SPECS:
        result = benchmark_model(
            spec,
            train_dataset,
            eval_dataset,
            test_dataset,
            args,
            output_dir,
        )
        results.append(result)

    df = pd.DataFrame(results)
    df_path = output_dir / "model_comparison.csv"
    df.to_csv(df_path, index=False)
    print(f"\nSaved comparison table to {df_path}")

    plot_metrics(df, output_dir)
    print(f"Artifacts saved under {output_dir}")


if __name__ == "__main__":
    main()
