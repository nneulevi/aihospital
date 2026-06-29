"""Metric helpers for binary hemorrhage classification."""

from __future__ import annotations

import math
from typing import Iterable


def binary_auc(labels: Iterable[int], scores: Iterable[float]) -> float | None:
    pairs = sorted(zip(scores, labels), key=lambda item: item[0])
    pos = sum(label == 1 for _, label in pairs)
    neg = sum(label == 0 for _, label in pairs)
    if pos == 0 or neg == 0:
        return None
    rank_sum = 0.0
    i = 0
    while i < len(pairs):
        j = i + 1
        while j < len(pairs) and math.isclose(pairs[j][0], pairs[i][0]):
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        rank_sum += avg_rank * sum(label == 1 for _, label in pairs[i:j])
        i = j
    return (rank_sum - pos * (pos + 1) / 2.0) / (pos * neg)


def classification_metrics(labels: list[int], scores: list[float], threshold: float = 0.5) -> dict[str, float | int | None]:
    preds = [1 if score >= threshold else 0 for score in scores]
    tp = sum(p == 1 and y == 1 for p, y in zip(preds, labels))
    tn = sum(p == 0 and y == 0 for p, y in zip(preds, labels))
    fp = sum(p == 1 and y == 0 for p, y in zip(preds, labels))
    fn = sum(p == 0 and y == 1 for p, y in zip(preds, labels))
    total = max(len(labels), 1)
    sensitivity = tp / max(tp + fn, 1)
    specificity = tn / max(tn + fp, 1)
    precision = tp / max(tp + fp, 1)
    npv = tn / max(tn + fn, 1)
    f1 = 2 * precision * sensitivity / max(precision + sensitivity, 1e-8)
    return {
        "auc": binary_auc(labels, scores),
        "accuracy": (tp + tn) / total,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "precision": precision,
        "npv": npv,
        "f1": f1,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "threshold": threshold,
        "count": len(labels),
    }
