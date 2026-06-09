# Best-of-N Hierarchical Skill Options

This repository is a controlled mechanism study for hierarchical robot/control models that plan over learned skills, options, or subgoals.

**Thesis.** Best-of-N high-level search can amplify option-boundary feasibility errors. As `N` grows, the selected abstract plan looks better under a learned proxy score, but it can become less executable because initiation sets, stochastic terminations, and inter-option handoffs are miscalibrated.

The repo includes a simulator, finite-N theory check, repair method, figures, tests, claim audit, and an anonymous ICLR-style paper draft.

## Quickstart

```powershell
python -m pip install -r requirements.txt
pytest
python -m bonoptions.experiments.run_smoke
python -m bonoptions.experiments.run_all
python -m bonoptions.experiments.run_claim_audit
.\scripts\build_paper.ps1
```

Main outputs:

- `results/all_selection.csv`
- `results/finite_n_validation.csv`
- `results/figures/bon_degradation.png`
- `results/figures/repair_comparison.png`
- `results/figures/controls.png`
- `docs/claims.md`
- `docs/final_audit.md`
- `paper/final/iclr_submission.pdf`

## What Is Implemented

- A synthetic option library with initiation neighborhoods, termination drift, reliable spans, and nominal rewards.
- A Best-of-N planner that samples high-level option sequences and selects the max proxy score.
- A learned proxy scorer with modes: `miscalibrated`, `calibrated`, `oracle`, `random`, and `anti_correlated`.
- Diagnostics for initiation violation, termination drift, reachability gap, boundary surprise, and chain executability estimate.
- Repair method: **Boundary-Calibrated Option Sieve**, which selects using public boundary evidence without hidden true labels.
- A finite-population order-statistic law for selected true utility under max-proxy selection.

## Claim Boundary

This is not a benchmark-scale robotics result. It is a controlled mechanism paper: the experiments test a specific architecture-level failure mode in option composition. The intended next step is to replace the hand-designed boundary diagnostics with learned estimators and evaluate on real robot skill-chain or long-horizon manipulation suites.

The paper should only claim what `python -m bonoptions.experiments.run_claim_audit` marks as passing.
