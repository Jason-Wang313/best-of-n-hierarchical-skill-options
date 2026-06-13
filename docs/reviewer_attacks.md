# Reviewer Attacks

## Attack: This Is Just Reward Model Overoptimization

Response: The paper agrees that proxy overoptimization is the broader family. The contribution is the option-specific mechanism: selection pressure concentrates on sequences with unsafe initiation margins, termination drift, and inter-option handoff surprise.

## Attack: The Simulator Is Too Simple

Response: Correct. This is a mechanism simulator, not a robot benchmark claim. The paper should be judged on whether the mechanism is clean, falsifiable, and useful enough to motivate benchmark validation.

## Attack: This Is One Hand-Designed Option Library

Response: The v3 pass adds a cross-library seed grid. The same fixed handoff-calibrated selector is evaluated across six independently sampled option libraries, with paired proxy-tail baselines and bootstrap intervals.

## Attack: One Boundary Diagnostic Carries The Result

Response: The v3 boundary-channel ablation tests initiation-only, termination-drift-only, reachability-only, boundary-surprise-only, and chain-estimate-only selectors. Full public handoff evidence beats the best single channel and reduces selected boundary risk more strongly.

## Attack: The Repair Is Hand-Engineered

Response: Handoff-Calibrated Sieve is a diagnostic repair, not a final robotics algorithm. It identifies the evidence that learned high-level planners need: initiation support, termination uncertainty, reachability, and handoff surprise.

## Attack: Learned Boundary Estimates Will Be Noisy

Response: The v3 diagnostic-noise experiment corrupts the public boundary estimate before selection. Moderate noise still helps, while severe noise sharply reduces recovery. The paper now states this as a failure boundary rather than hiding it.

## Attack: Oracle Controls Are Too Easy

Response: The oracle control is not a proposed method. It confirms that the degradation is not caused by larger candidate sets alone; it appears when proxy scoring is miscalibrated relative to feasibility.

## Attack: The Rank-Tail Law Is Modest

Response: Yes. The identity is intentionally exact and narrow. It links proxy-rank concentration to selected true utility when the high-proxy tail is unsafe; it is not presented as the main novelty.

## Attack: No Real Robot Results

Response: The claim boundary says this plainly. A benchmark extension should replace the synthetic option world with learned skills and evaluate whether the same boundary diagnostics predict execution failure.
