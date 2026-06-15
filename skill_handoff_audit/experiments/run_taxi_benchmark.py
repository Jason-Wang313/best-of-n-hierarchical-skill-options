from __future__ import annotations

import json
import shutil
from pathlib import Path
from statistics import mean
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from skill_handoff_audit.experiments.common import FIGURES, PAPER_FIGURES, RESULTS, ensure_dirs
from skill_handoff_audit.taxi_benchmark import (
    evaluate_candidate,
    sample_candidate_chains,
    select_handoff_sieve,
    taxi_initial_states,
)


N_GRID = (1, 2, 4, 8, 16, 32, 64)
TAXI_DIR = RESULTS / "taxi_option_benchmark"


def _ci(values: list[float], *, seed: int = 2027) -> dict[str, float]:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise ValueError("empty CI input")
    rng = np.random.default_rng(seed)
    draws = rng.choice(arr, size=(1200, arr.size), replace=True).mean(axis=1)
    return {
        "mean": float(arr.mean()),
        "lo": float(np.quantile(draws, 0.025)),
        "hi": float(np.quantile(draws, 0.975)),
        "std": float(arr.std(ddof=1)) if arr.size > 1 else 0.0,
        "n": float(arr.size),
    }


def _selected_rows(
    *,
    seed: int,
    context_id: int,
    obs: int,
    candidates,
    n: int,
) -> list[dict[str, Any]]:
    pool = list(candidates[: int(n)])
    methods = {
        "first_candidate": pool[0],
        "proxy_tail": max(pool, key=lambda cand: cand.proxy_score),
        "handoff_sieve": select_handoff_sieve(pool),
        "risk_only": min(pool, key=lambda cand: cand.diagnostics.public_boundary_risk),
        "oracle_tail": max(pool, key=lambda cand: cand.true_return),
    }
    rows: list[dict[str, Any]] = []
    for method, selected in methods.items():
        row = selected.public_row()
        row.update(
            {
                "benchmark": "Taxi-v3",
                "seed": int(seed),
                "context_id": int(context_id),
                "obs": int(obs),
                "N": int(n),
                "selector": method,
            }
        )
        rows.append(row)
    return rows


def _plot(rows: pd.DataFrame, out_path: Path) -> None:
    means = rows.groupby(["selector", "N"], as_index=False).mean(numeric_only=True)
    x_ticks = sorted(int(n) for n in rows["N"].unique())
    colors = {
        "first_candidate": "#777777",
        "proxy_tail": "#b23b3b",
        "handoff_sieve": "#1a8f5a",
        "risk_only": "#2f6fbb",
        "oracle_tail": "#111111",
    }
    fig, axes = plt.subplots(1, 3, figsize=(12.0, 3.5), constrained_layout=True)
    for selector, color in colors.items():
        sub = means[means["selector"] == selector].sort_values("N")
        axes[0].plot(sub["N"], sub["true_return"], marker="o", color=color, label=selector)
        axes[1].plot(sub["N"], sub["success"], marker="o", color=color)
        axes[2].plot(sub["N"], sub["public_boundary_risk"], marker="o", color=color)
    for ax in axes:
        ax.set_xscale("log", base=2)
        ax.set_xticks(x_ticks)
        ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
        ax.grid(True, alpha=0.25)
        ax.set_xlabel("candidate budget N")
    axes[1].set_ylim(-0.02, 1.05)
    axes[0].set_ylabel("Taxi return")
    axes[1].set_ylabel("delivery success")
    axes[2].set_ylabel("public handoff risk")
    axes[0].set_title("Executed utility")
    axes[1].set_title("Task completion")
    axes[2].set_title("Boundary evidence")
    axes[0].legend(frameon=False, fontsize=6.7)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def run_taxi_benchmark(
    *,
    preset: str = "full",
    seeds: list[int] | None = None,
    contexts_per_seed: int | None = None,
    output_dir: Path = TAXI_DIR,
) -> dict[str, Any]:
    ensure_dirs()
    seeds = [80, 81, 82, 83, 84] if seeds is None else [int(seed) for seed in seeds]
    contexts = 8 if preset == "smoke" else 16
    if contexts_per_seed is not None:
        contexts = int(contexts_per_seed)
    max_candidates = 16 if preset == "smoke" else 32
    n_values = tuple(n for n in N_GRID if n <= max_candidates)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    effect_rows: list[dict[str, Any]] = []
    for seed in seeds:
        states = taxi_initial_states(seed, contexts)
        for context_id, obs in enumerate(states):
            chains = sample_candidate_chains(obs, max_candidates, seed * 1000 + context_id)
            evaluated: dict[tuple[str, ...], Any] = {}
            candidates = []
            for chain in chains:
                chain_key = tuple(chain)
                if chain_key not in evaluated:
                    evaluated[chain_key] = evaluate_candidate(obs, chain_key)
                candidates.append(evaluated[chain_key])
            for n in n_values:
                rows.extend(_selected_rows(seed=seed, context_id=context_id, obs=obs, candidates=candidates, n=n))

        frame_seed = pd.DataFrame([row for row in rows if row["seed"] == seed and row["N"] == max(n_values)])
        pivot = frame_seed.pivot_table(
            index="context_id",
            columns="selector",
            values=["true_return", "success", "public_boundary_risk", "proxy_score"],
        )
        proxy = pivot["true_return"]["proxy_tail"]
        first = pivot["true_return"]["first_candidate"]
        sieve = pivot["true_return"]["handoff_sieve"]
        risk = pivot["true_return"]["risk_only"]
        oracle = pivot["true_return"]["oracle_tail"]
        effect_rows.append(
            {
                "benchmark": "Taxi-v3",
                "seed": int(seed),
                "proxy_minus_first_return": float((proxy - first).mean()),
                "sieve_minus_proxy_return": float((sieve - proxy).mean()),
                "risk_only_minus_proxy_return": float((risk - proxy).mean()),
                "oracle_minus_proxy_return": float((oracle - proxy).mean()),
                "sieve_minus_proxy_success": float(
                    (pivot["success"]["handoff_sieve"] - pivot["success"]["proxy_tail"]).mean()
                ),
                "sieve_minus_proxy_risk": float(
                    (pivot["public_boundary_risk"]["handoff_sieve"] - pivot["public_boundary_risk"]["proxy_tail"]).mean()
                ),
                "sieve_minus_proxy_score": float(
                    (pivot["proxy_score"]["handoff_sieve"] - pivot["proxy_score"]["proxy_tail"]).mean()
                ),
            }
        )

    metrics = pd.DataFrame(rows)
    effects = pd.DataFrame(effect_rows)
    metrics.to_csv(output_dir / "metrics.csv", index=False)
    effects.to_csv(output_dir / "effects.csv", index=False)
    figure_path = FIGURES / "taxi_option_benchmark.png"
    _plot(metrics, figure_path)
    shutil.copy2(figure_path, PAPER_FIGURES / figure_path.name)
    shutil.copy2(figure_path, output_dir / figure_path.name)

    proxy_harm = _ci(effects["proxy_minus_first_return"].astype(float).tolist())
    repair = _ci(effects["sieve_minus_proxy_return"].astype(float).tolist())
    risk_reduction = _ci(effects["sieve_minus_proxy_risk"].astype(float).tolist())
    success_repair = _ci(effects["sieve_minus_proxy_success"].astype(float).tolist())
    oracle = _ci(effects["oracle_minus_proxy_return"].astype(float).tolist())
    risk_only = _ci(effects["risk_only_minus_proxy_return"].astype(float).tolist())

    claims = {
        "taxi_proxy_tail_harms_return": proxy_harm["hi"] < -5.0,
        "taxi_handoff_sieve_repairs_return": repair["lo"] > 8.0,
        "taxi_handoff_sieve_success_noninferior": success_repair["mean"] >= -0.01,
        "taxi_handoff_sieve_reduces_public_risk": risk_reduction["hi"] < -1.0,
        "taxi_oracle_headroom_positive": oracle["lo"] > 10.0,
        "taxi_public_risk_control_repairs_return": risk_only["lo"] > 8.0,
    }
    payload = {
        "benchmark": "Taxi-v3",
        "preset": preset,
        "seeds": seeds,
        "contexts_per_seed": int(contexts),
        "n_values": list(n_values),
        "max_candidates": int(max_candidates),
        "metrics_rows": int(len(metrics)),
        "effect_rows": int(len(effects)),
        "summary": {
            "proxy_minus_first_return_ci": proxy_harm,
            "sieve_minus_proxy_return_ci": repair,
            "sieve_minus_proxy_success_ci": success_repair,
            "sieve_minus_proxy_risk_ci": risk_reduction,
            "oracle_minus_proxy_return_ci": oracle,
            "risk_only_minus_proxy_return_ci": risk_only,
        },
        "claims": claims,
        "all_passed": all(bool(v) for v in claims.values()),
    }
    with (output_dir / "aggregate.json").open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    print(json.dumps({"all_passed": payload["all_passed"], **payload["summary"]}, indent=2, sort_keys=True))
    return payload


def main() -> None:
    run_taxi_benchmark()


if __name__ == "__main__":
    main()
