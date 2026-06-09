# Final Audit

1. **Discovered main thesis.** Best-of-N high-level search over reusable robot options can amplify option-boundary feasibility errors: larger candidate budgets concentrate on plans that look ambitious under a learned subgoal proxy but violate initiation sets, termination distributions, and inter-option handoffs.

2. **What is genuinely new.** The contribution is not another generic reward-model overoptimization demo. It isolates an option-specific failure axis: proxy optimization increases selected boundary surprise and chain non-executability even when nominal abstract value rises.

3. **Theorem/proof that survived.** The finite-population order-statistic law for selected true utility survived adversarial checks and numerical Monte Carlo validation. It is deliberately modest: it characterizes a fixed proposal population under proxy max-selection, not all hierarchical planners.

4. **Strongest empirical result.** The raw Best-of-N curve raises proxy score while reducing executability at high N, matching the option-boundary thesis.

5. **Strongest repair result.** Boundary-Calibrated Option Sieve improves large-N true utility and executability using public boundary diagnostics only.

6. **Biggest weaknesses.** The environment is a controlled mechanism simulator, not a benchmark robot suite; the repair uses hand-designed boundary evidence; and the experiments validate the failure mode rather than claiming broad real-robot performance.

7. **Paper-worthiness.** Paper-worthy v1 as a mechanism paper, but it needs benchmark validation and learned boundary estimators before submission to a robotics-heavy venue.

8. **Final PDF location.** Expected repository path: `paper/final/iclr_submission.pdf`. Expected copied path: `C:\Users\wangz\Downloads\iclr_submission_hierarchical_options.pdf`.

## Claim Status

- `raw_proxy_increases_with_N`: pass (7.5208 vs 1.0000)
- `raw_executability_degrades`: pass (0.1516 vs 0.7200)
- `raw_true_utility_turns_down`: pass (-0.0773 vs 0.7800)
- `boundary_sieve_improves_large_N`: pass (0.5282 vs 0.0000)
- `oracle_control_does_not_show_failure`: pass (8.9836 vs 0.9500)
- `finite_N_law_matches_monte_carlo`: pass (0.0106 vs 0.0550)