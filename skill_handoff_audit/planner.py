from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from skill_handoff_audit.core import CandidatePlan, OptionWorld, SkillOption
from skill_handoff_audit.scoring import ProxyScorer


def _weighted_choice(
    rng: np.random.Generator, options: Sequence[SkillOption], weights: np.ndarray
) -> SkillOption:
    weights = np.asarray(weights, dtype=float)
    weights = np.maximum(weights, 1e-12)
    weights = weights / weights.sum()
    idx = int(rng.choice(len(options), p=weights))
    return options[idx]


@dataclass
class ProxyTailPlanner:
    world: OptionWorld
    scorer: ProxyScorer
    proposal_temperature: float = 0.62

    def sample_option_ids(self, horizon: int, rng: np.random.Generator) -> tuple[str, ...]:
        if horizon <= 0:
            raise ValueError("horizon must be positive")

        option_ids: list[str] = []
        current = self.world.start_state
        for _ in range(horizon):
            options = self.world.options
            distance = np.array([abs(option.init_center - current) for option in options])
            rewards = np.array([option.reward for option in options])
            spans = np.array([option.span for option in options])
            locality = np.exp(-distance / self.proposal_temperature)
            ambition = np.exp(0.24 * rewards + 0.09 * spans)
            weights = locality * ambition
            if rng.random() < 0.08:
                # Exploration produces occasional abstract jumps; proxy-tail
                # selection is what makes those rare high-proxy jumps matter.
                weights = 0.25 * weights + 0.75 * ambition
            option = _weighted_choice(rng, options, weights)
            option_ids.append(option.option_id)
            current = option.term_center
        return tuple(option_ids)

    def evaluate_option_ids(
        self, option_ids: Iterable[str], rng: np.random.Generator
    ) -> CandidatePlan:
        nominal_value, abstract_distance, true_exec, diagnostics = self.world.evaluate(option_ids)
        proxy = self.scorer.score(
            nominal_value=nominal_value,
            abstract_distance=abstract_distance,
            diagnostics=diagnostics,
            true_executability=true_exec,
            rng=rng,
        )
        true_utility = nominal_value * true_exec - 0.04 * diagnostics.option_count
        return CandidatePlan(
            option_ids=tuple(option_ids),
            nominal_value=nominal_value,
            abstract_distance=abstract_distance,
            proxy_score=float(proxy),
            diagnostics=diagnostics,
            true_executability=float(true_exec),
            true_utility=float(true_utility),
        )

    def generate_candidates(self, n: int, horizon: int, seed: int) -> list[CandidatePlan]:
        if n <= 0:
            raise ValueError("n must be positive")
        rng = np.random.default_rng(seed)
        candidates: list[CandidatePlan] = []
        for _ in range(n):
            option_ids = self.sample_option_ids(horizon=horizon, rng=rng)
            candidates.append(self.evaluate_option_ids(option_ids, rng=rng))
        return candidates

    def select_raw(self, candidates: Sequence[CandidatePlan]) -> CandidatePlan:
        if not candidates:
            raise ValueError("candidate list must be non-empty")
        return max(candidates, key=lambda plan: plan.proxy_score)

    def plan(self, n: int, horizon: int, seed: int) -> CandidatePlan:
        return self.select_raw(self.generate_candidates(n=n, horizon=horizon, seed=seed))


@dataclass(frozen=True)
class HandoffCalibratedSieve:
    """Repair method using only public option-boundary evidence."""

    penalty: float = 2.35
    max_public_risk: float | None = None
    min_chain_estimate: float = 0.02

    def public_boundary_score(self, plan: CandidatePlan) -> float:
        d = plan.diagnostics
        return (
            d.initiation_violation
            + 0.80 * d.termination_drift
            + 0.95 * d.reachability_gap
            + 0.65 * d.boundary_surprise
            - 0.35 * d.chain_executability_estimate
        )

    def rank_score(self, plan: CandidatePlan) -> float:
        return plan.proxy_score - self.penalty * self.public_boundary_score(plan)

    def select(self, candidates: Sequence[CandidatePlan]) -> CandidatePlan:
        if not candidates:
            raise ValueError("candidate list must be non-empty")

        eligible = [
            plan
            for plan in candidates
            if plan.diagnostics.chain_executability_estimate >= self.min_chain_estimate
            and (
                self.max_public_risk is None
                or plan.diagnostics.public_boundary_risk <= self.max_public_risk
            )
        ]
        pool = eligible if eligible else list(candidates)
        return max(pool, key=self.rank_score)


def rank_tail_selected_expectation(
    population: Sequence[CandidatePlan],
    ns: Iterable[int],
    metric: str = "true_utility",
) -> dict[int, float]:
    """Exact with-replacement law for utility after selecting the proxy-tail item.

    For a finite proposal population sampled uniformly with replacement, an item
    at proxy rank r is selected iff all N draws are at or below rank r and at
    least one draw is exactly rank r. With continuous proxy noise, ties are
    negligible; we break any remaining ties deterministically by stable sorting.
    """

    ordered = sorted(population, key=lambda plan: plan.proxy_score)
    m = len(ordered)
    if m == 0:
        raise ValueError("population must be non-empty")

    values = np.array([float(getattr(plan, metric)) for plan in ordered], dtype=float)
    out: dict[int, float] = {}
    ranks = np.arange(1, m + 1, dtype=float) / float(m)
    prev_ranks = np.arange(0, m, dtype=float) / float(m)
    for n in ns:
        if n <= 0:
            raise ValueError("N must be positive")
        probabilities = np.power(ranks, n) - np.power(prev_ranks, n)
        out[int(n)] = float(np.dot(probabilities, values))
    return out
