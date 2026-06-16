from __future__ import annotations

import json
import shutil
from pathlib import Path
from statistics import mean
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from skill_handoff_audit.core import CandidatePlan, OptionWorld
from skill_handoff_audit.experiments.common import FIGURES, PAPER_FIGURES, RESULTS, TABLES, ensure_dirs
from skill_handoff_audit.planner import ProxyTailPlanner
from skill_handoff_audit.scoring import ProxyScorer


FULL_COMPONENTS = (
    "initiation_violation",
    "termination_drift",
    "reachability_gap",
    "boundary_surprise",
    "chain_executability_estimate",
)

COMPONENT_SELECTORS = {
    "boundary_sieve_full": FULL_COMPONENTS,
    "initiation_only": ("initiation_violation",),
    "termination_drift_only": ("termination_drift",),
    "reachability_only": ("reachability_gap",),
    "boundary_surprise_only": ("boundary_surprise",),
    "chain_estimate_only": ("chain_executability_estimate",),
}

COMPONENT_WEIGHTS = {
    "initiation_violation": 1.00,
    "termination_drift": 0.80,
    "reachability_gap": 0.95,
    "boundary_surprise": 0.65,
    "chain_executability_estimate": -0.35,
}


def component_boundary_score(plan: CandidatePlan, components: Sequence[str] = FULL_COMPONENTS) -> float:
    diagnostics = plan.diagnostics
    score = 0.0
    for component in components:
        score += COMPONENT_WEIGHTS[component] * float(getattr(diagnostics, component))
    return float(score)


def select_with_component_score(
    candidates: Sequence[CandidatePlan],
    components: Sequence[str] = FULL_COMPONENTS,
    *,
    penalty: float = 2.35,
) -> CandidatePlan:
    if not candidates:
        raise ValueError("candidate list must be non-empty")
    return max(
        candidates,
        key=lambda plan: plan.proxy_score - penalty * component_boundary_score(plan, components),
    )


def select_with_noisy_boundary_estimate(
    candidates: Sequence[CandidatePlan],
    *,
    noise_scale: float,
    seed: int,
    penalty: float = 2.35,
) -> CandidatePlan:
    if not candidates:
        raise ValueError("candidate list must be non-empty")
    clean = np.array([component_boundary_score(plan, FULL_COMPONENTS) for plan in candidates], dtype=float)
    scale = float(np.std(clean))
    if scale < 1e-9:
        scale = 1.0
    rng = np.random.default_rng(seed)
    observed = clean + rng.normal(0.0, noise_scale * scale, size=len(candidates))
    best_idx = max(
        range(len(candidates)),
        key=lambda idx: candidates[idx].proxy_score - penalty * float(observed[idx]),
    )
    return candidates[int(best_idx)]


def _plan_row(
    *,
    dataset: str,
    selector: str,
    world_seed: int,
    seed: int,
    horizon: int,
    n: int,
    plan: CandidatePlan,
    noise_scale: float = -1.0,
    components: Sequence[str] | None = None,
) -> dict[str, float | int | str]:
    row = plan.public_row()
    row.update(
        {
            "dataset": dataset,
            "selector": selector,
            "world_seed": int(world_seed),
            "seed": int(seed),
            "horizon": int(horizon),
            "N": int(n),
            "noise_scale": float(noise_scale),
            "components": "+".join(components or ()),
        }
    )
    return row


def _candidate_pools(
    *,
    world_seeds: Iterable[int],
    seeds: Iterable[int],
    horizon: int,
    n: int,
) -> dict[tuple[int, int], list[CandidatePlan]]:
    pools: dict[tuple[int, int], list[CandidatePlan]] = {}
    for world_seed in world_seeds:
        world = OptionWorld.default(seed=int(world_seed))
        planner = ProxyTailPlanner(world=world, scorer=ProxyScorer(mode="miscalibrated"))
        for seed in seeds:
            pools[(int(world_seed), int(seed))] = planner.generate_candidates(
                n=int(n),
                horizon=int(horizon),
                seed=int(seed),
            )
    return pools


def run_handoff_robustness(
    *,
    n: int = 256,
    horizon: int = 4,
    ablation_seeds: Iterable[int] = range(12),
    library_world_seeds: Iterable[int] = range(6),
    library_seeds: Iterable[int] = range(8),
    noise_levels: Iterable[float] = (0.0, 0.25, 0.50, 1.00, 1.50),
    write_outputs: bool = True,
) -> pd.DataFrame:
    ensure_dirs()
    ablation_seed_list = [int(seed) for seed in ablation_seeds]
    library_world_seed_list = [int(seed) for seed in library_world_seeds]
    library_seed_list = [int(seed) for seed in library_seeds]
    noise_level_list = [float(level) for level in noise_levels]
    world_zero_seed_count = max(ablation_seed_list + library_seed_list) + 1

    pools: dict[tuple[int, int], list[CandidatePlan]] = {}
    pools.update(
        _candidate_pools(
            world_seeds=[0],
            seeds=range(world_zero_seed_count),
            horizon=horizon,
            n=n,
        )
    )
    nonzero_worlds = [seed for seed in library_world_seed_list if seed != 0]
    if nonzero_worlds:
        pools.update(
            _candidate_pools(
                world_seeds=nonzero_worlds,
                seeds=library_seed_list,
                horizon=horizon,
                n=n,
            )
        )

    rows: list[dict[str, float | int | str]] = []

    for seed in ablation_seed_list:
        candidates = pools[(0, seed)]
        raw = max(candidates, key=lambda plan: plan.proxy_score)
        rows.append(
            _plan_row(
                dataset="component_ablation",
                selector="proxy_tail",
                world_seed=0,
                seed=seed,
                horizon=horizon,
                n=n,
                plan=raw,
            )
        )
        for selector, components in COMPONENT_SELECTORS.items():
            selected = select_with_component_score(candidates, components)
            rows.append(
                _plan_row(
                    dataset="component_ablation",
                    selector=selector,
                    world_seed=0,
                    seed=seed,
                    horizon=horizon,
                    n=n,
                    plan=selected,
                    components=components,
                )
            )

    for seed in ablation_seed_list:
        candidates = pools[(0, seed)]
        raw = max(candidates, key=lambda plan: plan.proxy_score)
        for noise_scale in noise_level_list:
            selected = select_with_noisy_boundary_estimate(
                candidates,
                noise_scale=noise_scale,
                seed=9100 + int(100 * noise_scale) + seed,
            )
            rows.append(
                _plan_row(
                    dataset="diagnostic_noise",
                    selector="proxy_tail",
                    world_seed=0,
                    seed=seed,
                    horizon=horizon,
                    n=n,
                    plan=raw,
                    noise_scale=noise_scale,
                )
            )
            rows.append(
                _plan_row(
                    dataset="diagnostic_noise",
                    selector="noisy_boundary_sieve",
                    world_seed=0,
                    seed=seed,
                    horizon=horizon,
                    n=n,
                    plan=selected,
                    noise_scale=noise_scale,
                    components=FULL_COMPONENTS,
                )
            )

    for world_seed in library_world_seed_list:
        for seed in library_seed_list:
            candidates = pools[(world_seed, seed)]
            raw = max(candidates, key=lambda plan: plan.proxy_score)
            selected = select_with_component_score(candidates, FULL_COMPONENTS)
            rows.append(
                _plan_row(
                    dataset="library_seed_grid",
                    selector="proxy_tail",
                    world_seed=world_seed,
                    seed=seed,
                    horizon=horizon,
                    n=n,
                    plan=raw,
                )
            )
            rows.append(
                _plan_row(
                    dataset="library_seed_grid",
                    selector="boundary_sieve_full",
                    world_seed=world_seed,
                    seed=seed,
                    horizon=horizon,
                    n=n,
                    plan=selected,
                    components=FULL_COMPONENTS,
                )
            )

    df = pd.DataFrame(rows)
    if write_outputs:
        out_csv = RESULTS / "handoff_robustness.csv"
        df.to_csv(out_csv, index=False)
        _write_summary(df)
        _write_claim_payload(df)
        figure_paths = [
            FIGURES / "boundary_component_ablation.png",
            FIGURES / "diagnostic_noise_sensitivity.png",
            FIGURES / "library_seed_grid.png",
        ]
        plot_component_ablation(df, figure_paths[0])
        plot_noise_sensitivity(df, figure_paths[1])
        plot_library_grid(df, figure_paths[2])
        for path in figure_paths:
            shutil.copy2(path, PAPER_FIGURES / path.name)
        print(f"wrote {out_csv}")
        print(f"wrote robustness figures under {FIGURES}")
    return df


def _write_summary(df: pd.DataFrame) -> None:
    metrics = ["true_utility", "true_executability", "public_boundary_risk", "proxy_score"]
    summary = (
        df.groupby(["dataset", "selector", "world_seed", "horizon", "N", "noise_scale"], as_index=False)[
            metrics
        ]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    summary.to_csv(TABLES / "handoff_robustness_summary.csv", index=False)


def _bootstrap_ci(values: Sequence[float], *, seed: int = 717, repetitions: int = 2000) -> dict[str, float]:
    vals = np.asarray(values, dtype=float)
    if vals.size == 0:
        raise ValueError("cannot bootstrap an empty sample")
    rng = np.random.default_rng(seed)
    draws = rng.choice(vals, size=(repetitions, vals.size), replace=True).mean(axis=1)
    return {
        "mean": float(vals.mean()),
        "ci_low": float(np.quantile(draws, 0.025)),
        "ci_high": float(np.quantile(draws, 0.975)),
    }


def _paired_delta(
    df: pd.DataFrame,
    *,
    dataset: str,
    selector: str,
    baseline: str,
    metric: str,
    noise_scale: float | None = None,
) -> list[float]:
    sub = df[df["dataset"] == dataset].copy()
    if noise_scale is not None:
        sub = sub[np.isclose(sub["noise_scale"], float(noise_scale))]
    keys = ["dataset", "world_seed", "seed", "horizon", "N", "noise_scale"]
    left = sub[sub["selector"] == selector][keys + [metric]]
    right = sub[sub["selector"] == baseline][keys + [metric]]
    merged = left.merge(right, on=keys, suffixes=("_selected", "_baseline"))
    return (merged[f"{metric}_selected"] - merged[f"{metric}_baseline"]).astype(float).tolist()


def audit_robustness_claims(df: pd.DataFrame) -> dict:
    component = df[df["dataset"] == "component_ablation"]
    means = component.groupby("selector").mean(numeric_only=True)
    single_selectors = [
        "initiation_only",
        "termination_drift_only",
        "reachability_only",
        "boundary_surprise_only",
        "chain_estimate_only",
    ]
    best_single_utility = max(float(means.loc[name, "true_utility"]) for name in single_selectors)
    full_utility = float(means.loc["boundary_sieve_full", "true_utility"])
    raw_risk = float(means.loc["proxy_tail", "public_boundary_risk"])
    full_risk = float(means.loc["boundary_sieve_full", "public_boundary_risk"])

    library_utility_delta = _paired_delta(
        df,
        dataset="library_seed_grid",
        selector="boundary_sieve_full",
        baseline="proxy_tail",
        metric="true_utility",
    )
    library_exec_delta = _paired_delta(
        df,
        dataset="library_seed_grid",
        selector="boundary_sieve_full",
        baseline="proxy_tail",
        metric="true_executability",
    )
    noise_clean_delta = _paired_delta(
        df,
        dataset="diagnostic_noise",
        selector="noisy_boundary_sieve",
        baseline="proxy_tail",
        metric="true_utility",
        noise_scale=0.0,
    )
    noise_mid_delta = _paired_delta(
        df,
        dataset="diagnostic_noise",
        selector="noisy_boundary_sieve",
        baseline="proxy_tail",
        metric="true_utility",
        noise_scale=0.5,
    )
    noise_mid_exec_delta = _paired_delta(
        df,
        dataset="diagnostic_noise",
        selector="noisy_boundary_sieve",
        baseline="proxy_tail",
        metric="true_executability",
        noise_scale=0.5,
    )
    noise_severe_delta = _paired_delta(
        df,
        dataset="diagnostic_noise",
        selector="noisy_boundary_sieve",
        baseline="proxy_tail",
        metric="true_utility",
        noise_scale=1.5,
    )

    library_ci = _bootstrap_ci(library_utility_delta)
    mid_ci = _bootstrap_ci(noise_mid_delta)
    claims = {
        "component_full_beats_best_single_boundary_channel": {
            "status": "pass" if full_utility - best_single_utility > 0.04 else "fail",
            "value": full_utility - best_single_utility,
            "threshold": 0.04,
            "description": "Full handoff evidence beats the best single public boundary channel.",
        },
        "component_full_reduces_boundary_risk": {
            "status": "pass" if full_risk / max(raw_risk, 1e-9) < 0.75 else "fail",
            "value": full_risk / max(raw_risk, 1e-9),
            "threshold": 0.75,
            "description": "Full handoff evidence lowers selected public boundary risk relative to proxy tail.",
        },
        "library_seed_grid_repair_improves_mean": {
            "status": "pass" if library_ci["mean"] > 0.15 and mean(library_exec_delta) > 0.005 else "fail",
            "value": library_ci["mean"],
            "threshold": 0.15,
            "description": "The repair improves mean true utility across multiple independently sampled option libraries.",
            "ci_low": library_ci["ci_low"],
            "ci_high": library_ci["ci_high"],
        },
        "moderate_noisy_diagnostics_still_help": {
            "status": "pass" if mid_ci["mean"] > 0.05 and mean(noise_mid_exec_delta) > 0.003 else "fail",
            "value": mid_ci["mean"],
            "threshold": 0.05,
            "description": "Noisy public boundary estimates still improve selected utility at moderate noise.",
            "ci_low": mid_ci["ci_low"],
            "ci_high": mid_ci["ci_high"],
        },
        "severe_diagnostic_noise_exposes_failure_boundary": {
            "status": "pass" if mean(noise_clean_delta) - mean(noise_severe_delta) > 0.15 else "fail",
            "value": mean(noise_clean_delta) - mean(noise_severe_delta),
            "threshold": 0.15,
            "description": "Clean handoff diagnostics recover more value than severely corrupted diagnostics.",
        },
    }
    return {
        "robustness_path": str(RESULTS / "handoff_robustness.csv"),
        "all_passed": all(item["status"] == "pass" for item in claims.values()),
        "claims": claims,
    }


def _write_claim_payload(df: pd.DataFrame) -> None:
    payload = audit_robustness_claims(df)
    (RESULTS / "handoff_robustness_claims.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def plot_component_ablation(df: pd.DataFrame, out_path: Path) -> None:
    sub = df[df["dataset"] == "component_ablation"]
    order = ["proxy_tail"] + list(COMPONENT_SELECTORS)
    means = sub.groupby("selector").mean(numeric_only=True).reindex(order)
    labels = ["proxy", "full", "init", "drift", "reach", "surprise", "exec est."]
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 3.8), constrained_layout=True)
    axes[0].bar(labels, means["true_utility"], color="#4C78A8")
    axes[0].set_ylabel("selected true utility")
    axes[0].set_title("Boundary-channel ablation")
    axes[0].tick_params(axis="x", labelrotation=25)
    axes[1].bar(labels, means["public_boundary_risk"], color="#F58518")
    axes[1].set_ylabel("public boundary risk")
    axes[1].set_title("Full evidence suppresses unsafe handoffs")
    axes[1].tick_params(axis="x", labelrotation=25)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def plot_noise_sensitivity(df: pd.DataFrame, out_path: Path) -> None:
    sub = df[df["dataset"] == "diagnostic_noise"]
    rows = []
    for noise_scale in sorted(sub["noise_scale"].unique()):
        deltas = _paired_delta(
            sub,
            dataset="diagnostic_noise",
            selector="noisy_boundary_sieve",
            baseline="proxy_tail",
            metric="true_utility",
            noise_scale=float(noise_scale),
        )
        exec_deltas = _paired_delta(
            sub,
            dataset="diagnostic_noise",
            selector="noisy_boundary_sieve",
            baseline="proxy_tail",
            metric="true_executability",
            noise_scale=float(noise_scale),
        )
        rows.append(
            {
                "noise_scale": float(noise_scale),
                "utility_delta": mean(deltas),
                "executability_delta": mean(exec_deltas),
            }
        )
    curve = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(6.6, 4.0), constrained_layout=True)
    ax.plot(curve["noise_scale"], curve["utility_delta"], marker="o", label="true utility gain")
    ax.plot(
        curve["noise_scale"],
        curve["executability_delta"],
        marker="s",
        label="executability gain",
    )
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xlabel("diagnostic noise scale")
    ax.set_title("Estimated handoff evidence has a failure boundary")
    ax.legend(frameon=False)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def plot_library_grid(df: pd.DataFrame, out_path: Path) -> None:
    sub = df[df["dataset"] == "library_seed_grid"]
    means = sub.groupby(["world_seed", "selector"], as_index=False).mean(numeric_only=True)
    fig, ax = plt.subplots(figsize=(6.8, 4.0), constrained_layout=True)
    for selector, label in [("proxy_tail", "proxy tail"), ("boundary_sieve_full", "boundary sieve")]:
        curve = means[means["selector"] == selector]
        ax.plot(curve["world_seed"], curve["true_utility"], marker="o", label=label)
    ax.set_xlabel("option-library seed")
    ax.set_ylabel("selected true utility")
    ax.set_title("Repair across independently sampled option libraries")
    ax.legend(frameon=False)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def main() -> None:
    run_handoff_robustness()


if __name__ == "__main__":
    main()
