"""Weighted metrics and the paired circular block bootstrap over target dates (spec §6-§7)."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score


def wind_stats(err: np.ndarray, w: np.ndarray | None = None) -> dict:
    w = np.ones_like(err) if w is None else w
    sw = w.sum()
    if sw == 0:
        return {"mae": np.nan, "rmse": np.nan, "bias": np.nan}
    return {"mae": float((w * np.abs(err)).sum() / sw), "rmse": float(np.sqrt((w * err ** 2).sum() / sw)),
            "bias": float((w * err).sum() / sw)}


def confusion(y: np.ndarray, pred: np.ndarray, w: np.ndarray | None = None) -> dict:
    w = np.ones(len(y)) if w is None else w
    tp = float(w[(pred == 1) & (y == 1)].sum()); fp = float(w[(pred == 1) & (y == 0)].sum())
    fn = float(w[(pred == 0) & (y == 1)].sum()); tn = float(w[(pred == 0) & (y == 0)].sum())
    n = tp + fp + fn + tn
    prec = tp / (tp + fp) if tp + fp else np.nan
    rec = tp / (tp + fn) if tp + fn else np.nan
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else np.nan
    return {"tp": tp, "fn": fn, "fp": fp, "tn": tn, "n": n, "accuracy": (tp + tn) / n if n else np.nan,
            "precision": prec, "recall": rec, "f1": f1, "prevalence": (tp + fn) / n if n else np.nan,
            "all_negative_accuracy": (fp + tn) / n if n else np.nan}


def pr_auc(y: np.ndarray, p: np.ndarray, w: np.ndarray | None = None) -> float:
    if w is not None:
        m = w > 0
        y, p, w = y[m], p[m], w[m]
    if y.sum() == 0 or y.sum() == len(y):
        return np.nan
    return float(average_precision_score(y, p, sample_weight=w))


def brier(y: np.ndarray, p: np.ndarray, w: np.ndarray | None = None) -> float:
    w = np.ones(len(y)) if w is None else w
    return float((w * (p - y) ** 2).sum() / w.sum()) if w.sum() else np.nan


def block_weights(n_dates: int, block: int, B: int, seed: int):
    """Yield per-date multiplicities for B circular block resamples of n_dates sorted dates."""
    rng = np.random.default_rng(seed)
    k = int(np.ceil(n_dates / block))
    off = np.arange(block)
    for _ in range(B):
        starts = rng.integers(0, n_dates, k)
        idx = ((starts[:, None] + off) % n_dates).ravel()[:n_dates]
        yield np.bincount(idx, minlength=n_dates).astype(float)


def ci(values: list[float]) -> dict:
    a = np.asarray(values, dtype=float)
    ok = a[~np.isnan(a)]
    if len(ok) == 0:
        return {"lo": None, "hi": None, "undefined_resamples": int(len(a))}
    return {"lo": float(np.percentile(ok, 2.5)), "hi": float(np.percentile(ok, 97.5)),
            "undefined_resamples": int(len(a) - len(ok))}


def established(c: dict) -> str:
    if c["lo"] is None:
        return "undefined"
    if c["lo"] > 0:
        return "established: positive"
    if c["hi"] < 0:
        return "established: negative"
    return "no established difference"
