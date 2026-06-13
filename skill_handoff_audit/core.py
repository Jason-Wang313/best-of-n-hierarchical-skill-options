from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt
from typing import Iterable

import numpy as np


def sigmoid(x: float) -> float:
    """Numerically stable scalar sigmoid."""

    x = max(-60.0, min(60.0, x))
    return 1.0 / (1.0 + exp(-x))


@dataclass(frozen=True)
class SkillOption:
    """A one-dimensional abstraction of a robot skill/option.

    The state is an abstract task coordinate: e.g. pose progress, drawer opening,
    or object pose along a learned skill chain. The option has an initiation
    neighborhood, a stochastic termination distribution, and a span beyond which
    it becomes unreliable even if the high-level subgoal reward is attractive.
    """

    option_id: str
    init_center: float
    term_center: float
    init_radius: float
    term_sigma: float
    reward: float
    reliable_span: float

    @property
    def span(self) -> float:
        return abs(self.term_center - self.init_center)

    def initiation_probability(self, state_mean: float, state_sigma: float = 0.0) -> float:
        scale = 0.18 + 0.45 * state_sigma
        margin = self.init_radius - abs(state_mean - self.init_center)
        return sigmoid(margin / scale)

    def termination_mean(self, state_mean: float) -> float:
        # Starting outside the learned initiation manifold leaves a systematic
        # residual drift in the termination state.
        mismatch = state_mean - self.init_center
        return self.term_center + 0.18 * mismatch

    def termination_sample(self, rng: np.random.Generator, state_mean: float) -> float:
        return float(rng.normal(self.termination_mean(state_mean), self.term_sigma))


@dataclass(frozen=True)
class PlanDiagnostics:
    """Public boundary evidence available to a high-level option planner."""

    initiation_violation: float
    termination_drift: float
    reachability_gap: float
    boundary_surprise: float
    chain_executability_estimate: float
    option_count: int

    @property
    def public_boundary_risk(self) -> float:
        return (
            self.initiation_violation
            + 0.80 * self.termination_drift
            + 0.95 * self.reachability_gap
            + 0.65 * self.boundary_surprise
        )


@dataclass(frozen=True)
class CandidatePlan:
    """A generated option sequence with hidden true metrics and public evidence."""

    option_ids: tuple[str, ...]
    nominal_value: float
    abstract_distance: float
    proxy_score: float
    diagnostics: PlanDiagnostics
    true_executability: float
    true_utility: float

    def public_row(self) -> dict[str, float | str]:
        return {
            "plan": "->".join(self.option_ids),
            "nominal_value": self.nominal_value,
            "abstract_distance": self.abstract_distance,
            "proxy_score": self.proxy_score,
            "initiation_violation": self.diagnostics.initiation_violation,
            "termination_drift": self.diagnostics.termination_drift,
            "reachability_gap": self.diagnostics.reachability_gap,
            "boundary_surprise": self.diagnostics.boundary_surprise,
            "public_boundary_risk": self.diagnostics.public_boundary_risk,
            "chain_executability_estimate": self.diagnostics.chain_executability_estimate,
            "true_executability": self.true_executability,
            "true_utility": self.true_utility,
        }


class OptionWorld:
    """A controlled option library with safe local skills and risky long skills."""

    def __init__(self, options: Iterable[SkillOption], start_state: float = 0.0):
        self.options = tuple(options)
        self.start_state = float(start_state)
        self.by_id = {option.option_id: option for option in self.options}
        if len(self.by_id) != len(self.options):
            raise ValueError("option ids must be unique")

    @classmethod
    def default(cls, seed: int = 0) -> "OptionWorld":
        rng = np.random.default_rng(seed)
        options: list[SkillOption] = []
        for i, center in enumerate(np.linspace(0.0, 8.0, 9)):
            safe_span = 0.75 + 0.08 * rng.normal()
            options.append(
                SkillOption(
                    option_id=f"local_{i}",
                    init_center=float(center),
                    term_center=float(center + safe_span),
                    init_radius=float(0.92 + 0.04 * rng.normal()),
                    term_sigma=float(max(0.05, 0.10 + 0.02 * rng.normal())),
                    reward=float(1.05 + 0.09 * rng.normal()),
                    reliable_span=1.20,
                )
            )

            bridge_span = 1.35 + 0.10 * rng.normal()
            options.append(
                SkillOption(
                    option_id=f"bridge_{i}",
                    init_center=float(center + 0.05 * rng.normal()),
                    term_center=float(center + bridge_span),
                    init_radius=float(0.65 + 0.04 * rng.normal()),
                    term_sigma=float(max(0.08, 0.18 + 0.03 * rng.normal())),
                    reward=float(1.85 + 0.15 * rng.normal()),
                    reliable_span=1.55,
                )
            )

            leap_span = 2.25 + 0.20 * rng.normal()
            options.append(
                SkillOption(
                    option_id=f"leap_{i}",
                    init_center=float(center + 0.15 * rng.normal()),
                    term_center=float(center + leap_span),
                    init_radius=float(0.42 + 0.04 * rng.normal()),
                    term_sigma=float(max(0.16, 0.34 + 0.04 * rng.normal())),
                    reward=float(3.25 + 0.22 * rng.normal()),
                    reliable_span=1.62,
                )
            )
        return cls(options=options, start_state=0.0)

    def option_sequence(self, option_ids: Iterable[str]) -> tuple[SkillOption, ...]:
        return tuple(self.by_id[option_id] for option_id in option_ids)

    def evaluate(self, option_ids: Iterable[str]) -> tuple[float, float, float, PlanDiagnostics]:
        """Return nominal value, abstract distance, true executability, diagnostics."""

        sequence = self.option_sequence(option_ids)
        if not sequence:
            raise ValueError("option sequence must be non-empty")

        state_mean = self.start_state
        state_sigma = 0.05
        nominal_value = 0.0
        abstract_distance = 0.0
        exec_prob = 1.0
        initiation_violation = 0.0
        termination_drift = 0.0
        reachability_gap = 0.0
        boundary_surprise = 0.0

        for option in sequence:
            boundary_gap = max(0.0, abs(state_mean - option.init_center) - option.init_radius)
            span_gap = max(0.0, option.span - option.reliable_span)
            init_success = option.initiation_probability(state_mean, state_sigma)
            span_success = exp(-0.80 * span_gap)
            drift_success = exp(-0.42 * option.term_sigma)

            exec_prob *= init_success * span_success * drift_success
            nominal_value += option.reward
            abstract_distance += option.span
            initiation_violation += boundary_gap
            reachability_gap += span_gap
            termination_drift += option.term_sigma
            boundary_surprise += boundary_gap / max(option.init_radius, 1e-6)
            boundary_surprise += 0.35 * state_sigma

            next_mean = option.termination_mean(state_mean)
            state_sigma = sqrt((0.24 * state_sigma) ** 2 + option.term_sigma**2)
            state_mean = next_mean

        true_executability = float(max(0.0, min(1.0, exec_prob)))
        chain_estimate = float(
            exp(
                -0.62 * initiation_violation
                -0.32 * termination_drift
                -0.48 * reachability_gap
                -0.20 * boundary_surprise
            )
        )
        diagnostics = PlanDiagnostics(
            initiation_violation=float(initiation_violation),
            termination_drift=float(termination_drift),
            reachability_gap=float(reachability_gap),
            boundary_surprise=float(boundary_surprise),
            chain_executability_estimate=max(0.0, min(1.0, chain_estimate)),
            option_count=len(sequence),
        )
        return float(nominal_value), float(abstract_distance), true_executability, diagnostics
