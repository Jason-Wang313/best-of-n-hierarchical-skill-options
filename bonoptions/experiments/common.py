from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from bonoptions.core import CandidatePlan, OptionWorld
from bonoptions.planner import (
    BestOfNPlanner,
    BoundaryCalibratedOptionSieve,
    finite_n_selected_expectation,
)
from bonoptions.scoring import ProxyScorer


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"
TABLES = RESULTS / "tables"
DOCS = ROOT / "docs"
PAPER_FIGURES = ROOT / "paper" / "figures"


def ensure_dirs() -> None:
    for path in (RESULTS, FIGURES, TABLES, DOCS, PAPER_FIGURES):
        path.mkdir(parents=True, exist_ok=True)


def _row(
    *,
    dataset: str,
    mode: str,
    selector: str,
    horizon: int,
    seed: int,
    n: int,
    plan: CandidatePlan,
) -> dict[str, float | int | str]:
    row = plan.public_row()
    row.update(
        {
            "dataset": dataset,
            "mode": mode,
            "selector": selector,
            "horizon": horizon,
            "seed": seed,
            "N": int(n),
        }
    )
    return row


def run_selection_sweep(
    *,
    ns: Iterable[int],
    seeds: Iterable[int],
    horizon: int,
    mode: str = "miscalibrated",
    dataset: str = "selection",
    world_seed: int = 0,
    miscalibration: float = 1.25,
    include_repair: bool = True,
) -> pd.DataFrame:
    ensure_dirs()
    ns = sorted({int(n) for n in ns})
    if not ns:
        raise ValueError("ns must be non-empty")

    world = OptionWorld.default(seed=world_seed)
    scorer = ProxyScorer(mode=mode, miscalibration=miscalibration)
    planner = BestOfNPlanner(world=world, scorer=scorer)
    sieve = BoundaryCalibratedOptionSieve()
    rows: list[dict[str, float | int | str]] = []

    max_n = max(ns)
    for seed in seeds:
        candidates = planner.generate_candidates(n=max_n, horizon=horizon, seed=seed)
        for n in ns:
            subset = candidates[:n]
            raw = planner.select_raw(subset)
            rows.append(
                _row(
                    dataset=dataset,
                    mode=mode,
                    selector="raw_bon",
                    horizon=horizon,
                    seed=int(seed),
                    n=n,
                    plan=raw,
                )
            )
            if include_repair:
                repaired = sieve.select(subset)
                rows.append(
                    _row(
                        dataset=dataset,
                        mode=mode,
                        selector="boundary_sieve",
                        horizon=horizon,
                        seed=int(seed),
                        n=n,
                        plan=repaired,
                    )
                )
    return pd.DataFrame(rows)


def finite_n_validation(
    *,
    ns: Iterable[int],
    population_size: int = 3500,
    repetitions: int = 1600,
    seed: int = 123,
    horizon: int = 4,
) -> pd.DataFrame:
    ensure_dirs()
    ns = sorted({int(n) for n in ns})
    world = OptionWorld.default(seed=0)
    scorer = ProxyScorer(mode="miscalibrated", miscalibration=1.25)
    planner = BestOfNPlanner(world=world, scorer=scorer)
    population = planner.generate_candidates(n=population_size, horizon=horizon, seed=seed)
    exact = finite_n_selected_expectation(population, ns=ns, metric="true_utility")

    proxy = np.array([plan.proxy_score for plan in population])
    utility = np.array([plan.true_utility for plan in population])
    rng = np.random.default_rng(seed + 999)
    rows: list[dict[str, float | int | str]] = []

    for n in ns:
        selected = []
        for _ in range(repetitions):
            idx = rng.integers(0, population_size, size=n)
            best_local = idx[int(np.argmax(proxy[idx]))]
            selected.append(float(utility[best_local]))
        mc_mean = float(mean(selected))
        rows.append(
            {
                "N": int(n),
                "exact_expected_true_utility": exact[n],
                "mc_expected_true_utility": mc_mean,
                "abs_error": abs(exact[n] - mc_mean),
                "repetitions": repetitions,
                "population_size": population_size,
            }
        )
    return pd.DataFrame(rows)


def summarize_selection(df: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "proxy_score",
        "true_utility",
        "true_executability",
        "public_boundary_risk",
        "initiation_violation",
        "termination_drift",
        "reachability_gap",
    ]
    return (
        df.groupby(["dataset", "mode", "selector", "horizon", "N"], as_index=False)[metrics]
        .agg(["mean", "std", "count"])
        .reset_index()
    )


def _mean_curve(
    df: pd.DataFrame, *, dataset: str, mode: str, selector: str, horizon: int
) -> pd.DataFrame:
    sub = df[
        (df["dataset"] == dataset)
        & (df["mode"] == mode)
        & (df["selector"] == selector)
        & (df["horizon"] == horizon)
    ]
    return sub.groupby("N", as_index=False).mean(numeric_only=True)


def plot_degradation(df: pd.DataFrame, out_path: Path) -> None:
    raw = _mean_curve(df, dataset="selection", mode="miscalibrated", selector="raw_bon", horizon=4)
    repaired = _mean_curve(
        df, dataset="selection", mode="miscalibrated", selector="boundary_sieve", horizon=4
    )
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.6), constrained_layout=True)
    axes[0].plot(raw["N"], raw["proxy_score"], marker="o", label="proxy score")
    axes[0].plot(raw["N"], raw["true_utility"], marker="s", label="true utility")
    axes[0].set_xscale("log", base=2)
    axes[0].set_xlabel("Best-of-N budget")
    axes[0].set_ylabel("selected plan score")
    axes[0].set_title("Raw BoN selects the proxy tail")
    axes[0].legend(frameon=False)

    axes[1].plot(raw["N"], raw["true_executability"], marker="o", label="raw BoN")
    axes[1].plot(repaired["N"], repaired["true_executability"], marker="s", label="boundary sieve")
    axes[1].plot(raw["N"], raw["public_boundary_risk"], marker="^", label="raw boundary risk")
    axes[1].set_xscale("log", base=2)
    axes[1].set_xlabel("Best-of-N budget")
    axes[1].set_title("Boundary feasibility is the failing axis")
    axes[1].legend(frameon=False)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def plot_repair(df: pd.DataFrame, out_path: Path) -> None:
    raw = _mean_curve(df, dataset="selection", mode="miscalibrated", selector="raw_bon", horizon=4)
    repaired = _mean_curve(
        df, dataset="selection", mode="miscalibrated", selector="boundary_sieve", horizon=4
    )
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.6), constrained_layout=True)
    axes[0].plot(raw["N"], raw["true_utility"], marker="o", label="raw BoN")
    axes[0].plot(repaired["N"], repaired["true_utility"], marker="s", label="boundary sieve")
    axes[0].set_xscale("log", base=2)
    axes[0].set_xlabel("Best-of-N budget")
    axes[0].set_ylabel("true utility")
    axes[0].set_title("Repair recovers executable value")
    axes[0].legend(frameon=False)

    axes[1].plot(raw["N"], raw["public_boundary_risk"], marker="o", label="raw BoN")
    axes[1].plot(repaired["N"], repaired["public_boundary_risk"], marker="s", label="boundary sieve")
    axes[1].set_xscale("log", base=2)
    axes[1].set_xlabel("Best-of-N budget")
    axes[1].set_ylabel("public boundary risk")
    axes[1].set_title("Sieve suppresses unsafe handoffs")
    axes[1].legend(frameon=False)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def plot_controls(df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.4, 4.0), constrained_layout=True)
    for mode in ["miscalibrated", "calibrated", "oracle", "random", "anti_correlated"]:
        sub = _mean_curve(df, dataset="selection", mode=mode, selector="raw_bon", horizon=4)
        if not sub.empty:
            ax.plot(sub["N"], sub["true_utility"], marker="o", label=mode)
    ax.set_xscale("log", base=2)
    ax.set_xlabel("Best-of-N budget")
    ax.set_ylabel("selected true utility")
    ax.set_title("Controls isolate proxy-boundary miscalibration")
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def plot_finite_law(df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.2, 3.8), constrained_layout=True)
    ax.plot(df["N"], df["exact_expected_true_utility"], marker="o", label="finite-N law")
    ax.plot(df["N"], df["mc_expected_true_utility"], marker="s", linestyle="--", label="Monte Carlo")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("Best-of-N budget")
    ax.set_ylabel("E[selected true utility]")
    ax.set_title("Finite-population order-statistic law")
    ax.legend(frameon=False)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
