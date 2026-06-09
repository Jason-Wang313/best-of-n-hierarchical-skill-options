# Reviewer Attacks

## Attack: This Is Just Reward Model Overoptimization

Response: The paper agrees that Best-of-N proxy overoptimization is the broader family. The contribution is the option-specific mechanism: selection pressure concentrates on sequences with unsafe initiation margins, termination drift, and inter-option handoff surprise.

## Attack: The Simulator Is Too Simple

Response: Correct. This is a mechanism simulator, not a robot benchmark claim. The paper should be judged on whether the mechanism is clean, falsifiable, and useful enough to motivate benchmark validation.

## Attack: The Repair Is Hand-Engineered

Response: Boundary-Calibrated Option Sieve is a diagnostic repair, not a final robotics algorithm. It identifies the evidence that learned high-level planners need: initiation support, termination uncertainty, reachability, and handoff surprise.

## Attack: Oracle Controls Are Too Easy

Response: The oracle control is not a proposed method. It confirms that the degradation is not caused by larger candidate sets alone; it appears when proxy scoring is miscalibrated relative to feasibility.

## Attack: The Theorem Is Modest

Response: Yes. The theorem is intentionally exact and narrow. It provides the finite-N selection law that links proxy rank concentration to true-utility degradation when the high-proxy tail is unsafe.

## Attack: No Real Robot Results

Response: The claim boundary says this plainly. A benchmark extension should replace the synthetic option world with learned skills and evaluate whether the same boundary diagnostics predict execution failure.
