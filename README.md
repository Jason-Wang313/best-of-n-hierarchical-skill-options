# Handoff-Feasibility Audits for Hierarchical Skill Chains

This repository is a controlled mechanism study for hierarchical robot/control systems that plan over learned skills, options, or subgoals.

**Thesis.** Proxy-tail planning can amplify handoff feasibility errors. As candidate budget `N` grows, the selected abstract plan may look better under a learned proxy score while becoming less executable because initiation sets, stochastic terminations, and inter-option handoffs are miscalibrated.

The repo includes a simulator, rank-tail calibration check, handoff-calibrated repair, figures, tests, claim audit, and an anonymous ICLR-style paper draft.

## Quickstart

```powershell
python -m pip install -r requirements.txt
pytest
python -m skill_handoff_audit.experiments.run_smoke
python -m skill_handoff_audit.experiments.run_all
python -m skill_handoff_audit.experiments.run_claim_audit
.\scripts\build_paper.ps1
```

Main outputs:

- `results/all_selection.csv`
- `results/finite_n_validation.csv`
- `results/figures/handoff_tail_degradation.png`
- `results/figures/repair_comparison.png`
- `results/figures/controls.png`
- `docs/claims.md`
- `docs/final_audit.md`
- `paper/final/iclr_submission.pdf`
- `C:\Users\wangz\OneDrive\Desktop\best of n hierarchical skill options-v2.pdf`

## What Is Implemented

- A synthetic option library with initiation neighborhoods, termination drift, reliable spans, and nominal rewards.
- A proxy-tail planner that samples high-level option sequences and selects the highest proxy-scoring chain.
- Proxy scorer modes: `miscalibrated`, `calibrated`, `oracle`, `random`, and `anti_correlated`.
- Diagnostics for initiation violation, termination drift, reachability gap, boundary surprise, and chain executability estimate.
- Repair method: **Handoff-Calibrated Sieve**, which selects using public boundary evidence without hidden true labels.
- A finite-population rank-tail calibration check for selected true utility under proxy-tail selection.

## Claim Boundary

This is not a benchmark-scale robotics result. It is a controlled mechanism paper: the experiments test a specific architecture-level failure mode in option composition. The intended next step is to replace the hand-designed boundary diagnostics with learned estimators and evaluate on real robot skill-chain or long-horizon manipulation suites.

The paper should only claim what `python -m skill_handoff_audit.experiments.run_claim_audit` marks as passing.
