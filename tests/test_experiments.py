import inspect

from skill_handoff_audit.experiments.common import finite_n_validation, run_selection_sweep
from skill_handoff_audit.experiments.run_handoff_robustness import (
    FULL_COMPONENTS,
    run_handoff_robustness,
    select_with_component_score,
    select_with_noisy_boundary_estimate,
)
from skill_handoff_audit.core import OptionWorld
from skill_handoff_audit.planner import ProxyTailPlanner
from skill_handoff_audit.scoring import ProxyScorer


def test_smoke_sweep_contains_raw_and_repair() -> None:
    df = run_selection_sweep(
        ns=[1, 4],
        seeds=range(2),
        horizon=3,
        mode="miscalibrated",
        dataset="test",
        include_repair=True,
    )
    assert set(df["selector"]) == {"proxy_tail", "boundary_sieve"}
    assert set(df["N"]) == {1, 4}


def test_finite_n_validation_is_close_to_monte_carlo() -> None:
    df = finite_n_validation(ns=[1, 4], population_size=300, repetitions=250, seed=5, horizon=3)
    assert float(df["abs_error"].mean()) < 0.18


def test_robustness_runner_has_three_datasets() -> None:
    df = run_handoff_robustness(
        n=24,
        ablation_seeds=range(2),
        library_world_seeds=range(2),
        library_seeds=range(2),
        noise_levels=(0.0, 0.5),
        write_outputs=False,
    )
    assert set(df["dataset"]) == {"component_ablation", "diagnostic_noise", "library_seed_grid"}
    assert {"proxy_tail", "boundary_sieve_full", "noisy_boundary_sieve"}.issubset(set(df["selector"]))


def test_noisy_boundary_selector_uses_public_evidence_only() -> None:
    source = inspect.getsource(select_with_component_score)
    source += inspect.getsource(select_with_noisy_boundary_estimate)
    assert "true_" not in source

    planner = ProxyTailPlanner(OptionWorld.default(seed=0), ProxyScorer(mode="miscalibrated"))
    candidates = planner.generate_candidates(n=24, horizon=3, seed=8)
    selected = select_with_component_score(candidates, FULL_COMPONENTS)
    noisy = select_with_noisy_boundary_estimate(candidates, noise_scale=0.5, seed=12)
    assert selected in candidates
    assert noisy in candidates
