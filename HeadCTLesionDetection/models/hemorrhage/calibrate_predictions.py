"""Build VinBigData probability calibration files from prediction rows."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable

try:
    from .metrics import classification_metrics
except ImportError:  # pragma: no cover - direct script fallback.
    from metrics import classification_metrics


def _float_value(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_label(value: Any) -> int | None:
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "positive"}:
        return 1
    if text in {"0", "false", "no", "negative"}:
        return 0
    return None


def _threshold_grid() -> list[float]:
    return [round(index / 100, 2) for index in range(1, 100)]


def _valid_scores(rows: Iterable[dict[str, Any]]) -> list[float]:
    scores = []
    for row in rows:
        score = _float_value(row.get("positive_probability") or row.get("confidence"))
        if score is not None:
            scores.append(max(0.0, min(1.0, score)))
    return scores


def calibrate_supervised(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels: list[int] = []
    scores: list[float] = []
    for row in rows:
        label = _int_label(row.get("label") if row.get("label") not in {None, ""} else row.get("hemorrhage"))
        score = _float_value(row.get("positive_probability") or row.get("confidence"))
        if label is None or score is None:
            continue
        labels.append(label)
        scores.append(max(0.0, min(1.0, score)))
    if not labels:
        raise ValueError("supervised calibration requires label/hemorrhage and positive_probability columns")

    candidates = []
    for threshold in _threshold_grid():
        metrics = classification_metrics(labels, scores, threshold)
        candidates.append(metrics)
    best = max(
        candidates,
        key=lambda item: (
            float(item["f1"] or 0.0),
            float(item["sensitivity"] or 0.0),
            float(item["specificity"] or 0.0),
        ),
    )
    return {
        "source": "cq500ct200_supervised",
        "recommended_threshold": float(best["threshold"]),
        "uncertainty_margin": 0.05,
        "metrics": best,
        "sample_count": len(labels),
        "positive_count": sum(labels),
        "negative_count": len(labels) - sum(labels),
        "limitations": [],
    }


def calibrate_unsupervised(rows: list[dict[str, Any]], percentile: int = 95) -> dict[str, Any]:
    scores = sorted(_valid_scores(rows))
    if not scores:
        raise ValueError("unsupervised calibration requires positive_probability/confidence values")
    percentile = max(1, min(99, int(percentile)))
    index = min(len(scores) - 1, max(0, round((percentile / 100) * (len(scores) - 1))))
    threshold = scores[index]
    return {
        "source": "cq500ct200_unsupervised_distribution",
        "recommended_threshold": float(threshold),
        "uncertainty_margin": 0.05,
        "metrics": {},
        "sample_count": len(scores),
        "positive_count": None,
        "negative_count": None,
        "limitations": [
            "该阈值仅来自当前数据概率分布，不含人工或官方标签，不能作为模型准确率、敏感度或特异度证据。",
        ],
    }


def load_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8") as file_obj:
            for line in file_obj:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows
    with path.open("r", encoding="utf-8-sig", newline="") as file_obj:
        return list(csv.DictReader(file_obj))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate VinBigData probabilities from prediction CSV/JSONL.")
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=["auto", "supervised", "unsupervised"], default="auto")
    parser.add_argument("--percentile", type=int, default=95)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_rows(args.predictions)
    supervised_possible = any(
        _int_label(row.get("label") if row.get("label") not in {None, ""} else row.get("hemorrhage")) is not None
        for row in rows
    )
    if args.mode == "supervised" or (args.mode == "auto" and supervised_possible):
        payload = calibrate_supervised(rows)
    else:
        payload = calibrate_unsupervised(rows, percentile=args.percentile)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
