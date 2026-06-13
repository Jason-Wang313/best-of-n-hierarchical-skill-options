import inspect

from skill_handoff_audit.core import OptionWorld
from skill_handoff_audit.planner import (
    ProxyTailPlanner,
    HandoffCalibratedSieve,
    rank_tail_selected_expectation,
)
from skill_handoff_audit.scoring import ProxyScorer


def test_planner_generates_exact_budget() -> None:
    planner = ProxyTailPlanner(OptionWorld.default(seed=0), ProxyScorer())
    candidates = planner.generate_candidates(n=7, horizon=3, seed=11)
    assert len(candidates) == 7
    assert all(len(plan.option_ids) == 3 for plan in candidates)


def test_proxy_and_true_utility_are_separate_quantities() -> None:
    planner = ProxyTailPlanner(OptionWorld.default(seed=0), ProxyScorer(mode="miscalibrated"))
    candidates = planner.generate_candidates(n=64, horizon=4, seed=4)
    raw = planner.select_raw(candidates)
    best_true = max(candidates, key=lambda plan: plan.true_utility)
    assert raw.proxy_score >= best_true.proxy_score
    assert raw.option_ids != best_true.option_ids or raw.true_utility != best_true.true_utility


def test_boundary_sieve_does_not_reference_hidden_true_labels() -> None:
    source = inspect.getsource(HandoffCalibratedSieve.public_boundary_score)
    source += inspect.getsource(HandoffCalibratedSieve.rank_score)
    source += inspect.getsource(HandoffCalibratedSieve.select)
    assert "true_" not in source


def test_boundary_sieve_can_choose_lower_proxy_safer_plan() -> None:
    planner = ProxyTailPlanner(OptionWorld.default(seed=0), ProxyScorer(mode="miscalibrated"))
    candidates = planner.generate_candidates(n=256, horizon=4, seed=2)
    raw = planner.select_raw(candidates)
    repaired = HandoffCalibratedSieve().select(candidates)
    assert repaired.proxy_score <= raw.proxy_score
    assert repaired.diagnostics.public_boundary_risk <= raw.diagnostics.public_boundary_risk


def test_rank_tail_calibration_matches_manual_two_item_population() -> None:
    planner = ProxyTailPlanner(OptionWorld.default(seed=0), ProxyScorer(mode="miscalibrated"))
    candidates = sorted(planner.generate_candidates(n=2, horizon=2, seed=9), key=lambda p: p.proxy_score)
    expected = rank_tail_selected_expectation(candidates, ns=[1, 2], metric="true_utility")
    low, high = candidates
    assert expected[1] == (low.true_utility + high.true_utility) / 2
    assert expected[2] == 0.25 * low.true_utility + 0.75 * high.true_utility
