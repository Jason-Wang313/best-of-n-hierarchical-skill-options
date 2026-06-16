# Final Audit

## Final Artifact and Provenance

- Paper: `best of n hierarchical skill options-v4.pdf`
- Source folder: `C:\Users\wangz\best of n hierarchical skill options`
- GitHub remote: `https://github.com/Jason-Wang313/best-of-n-hierarchical-skill-options.git`
- Repository PDF: `paper/final/best of n hierarchical skill options-v4.pdf`
- Visible Desktop PDF: `C:\Users\wangz\OneDrive\Desktop\best of n hierarchical skill options-v4.pdf`
- SHA256: `8AADB8F83EDA15C6A35B211048BF7355D41571B3A32A3BB1FE6DDE0769A73604`
- Page count: 11
- Repo/Desktop hash match: yes
- Verified on: 2026-06-16

## Final Verification

```powershell
python -m compileall skill_handoff_audit scripts tests -q
python -m skill_handoff_audit.experiments.run_taxi_benchmark
python -m skill_handoff_audit.experiments.run_claim_audit
python -m pytest -q
powershell -ExecutionPolicy Bypass -File scripts\build_paper.ps1 -DesktopCopy "C:\Users\wangz\OneDrive\Desktop\best of n hierarchical skill options-v4.pdf"
rg -n "undefined|Citation.*undefined|Reference.*undefined|Rerun to get|Overfull|LaTeX Warning|Package natbib Warning" "paper\main.log" "paper\final\pdflatex_3.log"
pdfinfo "paper\final\best of n hierarchical skill options-v4.pdf"
pdftoppm -png "paper\final\best of n hierarchical skill options-v4.pdf" "tmp\pdfs\hierarchical_v4\page"
```

Results:

- Compile check: passed.
- Taxi-v3 expanded benchmark: passed with 24 starts per seed and candidate budgets through `N=64`.
- Claim audit: all claims passed.
- Unit tests: 14 passed.
- Final LaTeX pass: no unresolved citations, unresolved references, rerun warnings, overfull boxes, or natbib warnings.
- PDF render: all 11 pages rendered.
- Visual QA: pages 1, 4, 5, 6, 7, 8, 9, 10, and 11 inspected for title/abstract, main figures, Taxi figure/table, claim ledger, references, appendix tail, clipping, and readability.

1. **Discovered main thesis.** Proxy-tail planning over reusable robot options can amplify handoff feasibility errors: larger candidate budgets concentrate on plans that look ambitious under a learned subgoal proxy but violate initiation sets, termination distributions, and inter-option handoffs.

2. **What is genuinely new.** The contribution is not another generic reward-model overoptimization demo. It isolates an option-specific failure axis: proxy optimization increases selected boundary surprise and chain non-executability even when nominal abstract value rises.

3. **Rank-tail calibration check that survived.** The finite-population rank-tail law for selected true utility survived adversarial checks and numerical Monte Carlo validation. It is deliberately modest: it characterizes a fixed proposal population under proxy-tail selection, not all hierarchical planners.

4. **Strongest empirical result.** The proxy-tail curve raises proxy score while reducing executability at high N, matching the handoff-boundary thesis.

5. **Strongest repair result.** Handoff-Calibrated Sieve improves large-budget true utility and executability using public boundary diagnostics only.

6. **V3 robustness result.** The expanded pass adds boundary-channel ablations, six independently sampled option-library seeds, and noisy diagnostic-estimator sensitivity. Full handoff evidence beats any single channel, cross-library repair has a positive bootstrap interval, and severe diagnostic noise exposes the expected failure boundary.

7. **V4 real benchmark result.** Gymnasium Taxi-v3 is included as a standard option-chain benchmark. Under the expanded held-out protocol, proxy-tail selection prefers illegal or badly ordered pickup/dropoff handoffs, while Handoff-Calibrated Sieve recovers executed return and keeps delivery success noninferior using public boundary evidence.

8. **Biggest weaknesses.** Taxi-v3 is a standard benchmark but still not a robotics-scale manipulation suite; the repair uses hand-designed boundary evidence; and the experiments validate the failure mode rather than claiming broad real-robot performance.

9. **Paper-worthiness.** Submission-ready as a mechanism paper after the v4 pass, with a standard benchmark tier, a clear claim boundary, and learned-boundary estimators reserved for future work.

10. **Final PDF location.** Expected repository path: `paper/final/best of n hierarchical skill options-v4.pdf`. The visible Desktop copy is produced with `scripts\build_paper.ps1 -DesktopCopy` after verification.

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
- `taxi_proxy_tail_harms_return`: pass (-12.6333 vs -5.0000)
- `taxi_handoff_sieve_repairs_return`: pass (11.0500 vs 8.0000)
- `taxi_handoff_sieve_success_noninferior`: pass (0.0000 vs -0.0100)
- `taxi_handoff_sieve_reduces_public_risk`: pass (-2.4247 vs -1.0000)
- `taxi_oracle_headroom_positive`: pass (12.6333 vs 10.0000)
- `taxi_public_risk_control_repairs_return`: pass (12.4000 vs 8.0000)
