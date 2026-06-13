# Final Audit

1. **Discovered main thesis.** Proxy-tail planning over reusable robot options can amplify handoff feasibility errors: larger candidate budgets concentrate on plans that look ambitious under a learned subgoal proxy but violate initiation sets, termination distributions, and inter-option handoffs.

2. **What is genuinely new.** The contribution is not another generic reward-model overoptimization demo. It isolates an option-specific failure axis: proxy optimization increases selected boundary surprise and chain non-executability even when nominal abstract value rises.

3. **Rank-tail calibration check that survived.** The finite-population rank-tail law for selected true utility survived adversarial checks and numerical Monte Carlo validation. It is deliberately modest: it characterizes a fixed proposal population under proxy-tail selection, not all hierarchical planners.

4. **Strongest empirical result.** The proxy-tail curve raises proxy score while reducing executability at high N, matching the handoff-boundary thesis.

5. **Strongest repair result.** Handoff-Calibrated Sieve improves large-budget true utility and executability using public boundary diagnostics only.

6. **V3 robustness result.** The expanded pass adds boundary-channel ablations, six independently sampled option-library seeds, and noisy diagnostic-estimator sensitivity. Full handoff evidence beats any single channel, cross-library repair has a positive bootstrap interval, and severe diagnostic noise exposes the expected failure boundary.

7. **Biggest weaknesses.** The environment is a controlled mechanism simulator, not a benchmark robot suite; the repair uses hand-designed boundary evidence; and the experiments validate the failure mode rather than claiming broad real-robot performance.

8. **Paper-worthiness.** Submission-ready as a mechanism paper after the v3 pass, with a clear claim boundary. It still needs benchmark validation and learned boundary estimators before claiming robotics-scale performance.

9. **Final PDF location.** Expected repository path: `paper/final/best of n hierarchical skill options-v3.pdf`. Desktop publication is a post-verification step only.

## Claim Status

- `raw_proxy_increases_with_N`: pass (7.5208 vs 1.0000)
- `raw_executability_degrades`: pass (0.1516 vs 0.7200)
- `raw_true_utility_turns_down`: pass (-0.0773 vs 0.7800)
- `boundary_sieve_improves_large_N`: pass (0.5282 vs 0.0000)
- `oracle_control_does_not_show_failure`: pass (8.9836 vs 0.9500)
- `rank_tail_calibration_matches_monte_carlo`: pass (0.0106 vs 0.0550)
- `component_full_beats_best_single_boundary_channel`: pass (0.1164 vs 0.0400)
- `component_full_reduces_boundary_risk`: pass (0.5815 vs 0.7500)
- `library_seed_grid_repair_improves_mean`: pass (0.4181 vs 0.1500)
- `moderate_noisy_diagnostics_still_help`: pass (0.7987 vs 0.0500)
- `severe_diagnostic_noise_exposes_failure_boundary`: pass (0.3878 vs 0.1500)