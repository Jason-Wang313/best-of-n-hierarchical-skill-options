from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bonoptions.core import PlanDiagnostics


@dataclass(frozen=True)
class ProxyScorer:
    """Learned high-level scorer with controllable feasibility miscalibration."""

    mode: str = "miscalibrated"
    miscalibration: float = 1.25
    noise_std: float = 0.16

    def score(
        self,
        *,
        nominal_value: float,
        abstract_distance: float,
        diagnostics: PlanDiagnostics,
        true_executability: float,
        rng: np.random.Generator,
    ) -> float:
        noise = float(rng.normal(0.0, self.noise_std))

        if self.mode == "oracle":
            return nominal_value * true_executability + noise * 0.05
        if self.mode == "random":
            return float(rng.normal(0.0, 1.0))
        if self.mode == "anti_correlated":
            return (
                nominal_value
                + 1.75 * diagnostics.public_boundary_risk
                - 5.0 * true_executability
                + noise
            )
        if self.mode == "calibrated":
            return nominal_value - 2.15 * diagnostics.public_boundary_risk + noise
        if self.mode != "miscalibrated":
            raise ValueError(f"unknown scorer mode: {self.mode}")

        ambitious_subgoal_bonus = 0.30 * abstract_distance + 0.70 * diagnostics.reachability_gap
        soft_penalty = (1.0 - self.miscalibration) * diagnostics.public_boundary_risk
        return nominal_value + self.miscalibration * ambitious_subgoal_bonus + soft_penalty + noise
