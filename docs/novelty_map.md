# Novelty Map

## Search Scope

This map was written after reviewing the governing prompt, classic options literature, recent proxy-overoptimization work, and ICLR formatting requirements. Useful anchors:

- ICLR 2026 Author Guide: https://iclr.cc/Conferences/2026/AuthorGuide
- ICLR Master-Template repository: https://github.com/ICLR/Master-Template
- Sutton, Precup, and Singh (1999), options and temporal abstraction.
- Bacon, Harb, and Precup (2017), option-critic.
- Gao, Schulman, and Hilton (2023), reward model overoptimization.
- Recent initiation-set work, including OpenReview entry "Effectively Learning Initiation Sets in Hierarchical Reinforcement Learning".

## What Is Already Known

Options are defined by initiation sets, policies, and termination conditions. The literature already recognizes that initiation sets and termination behavior matter for temporal abstraction, and many hierarchical RL methods learn or discover options.

Proxy overoptimization is also known: selecting strongly against an imperfect learned score can overfit proxy error and hurt ground-truth quality.

Robot skill chaining already worries about preconditions, postconditions, and handoff feasibility.

## What Would Be Incremental

- Showing a generic Goodhart curve for hierarchical planners with no option-specific mechanism.
- Re-ranking option plans by a learned reward model and calling degradation "reward hacking".
- Adding a feasibility penalty without explaining why proxy-tail planning makes boundary errors worse.

## What Looks Genuinely New Here

The sharp angle is the interaction between proxy-tail planning and **option-boundary evidence**. The selected high-level plan becomes risky not because each skill is bad in isolation, but because proxy-tail selection concentrates on rare abstract sequences whose initiation margins, termination distributions, and next-option handoffs are jointly miscalibrated.

The mechanism is architecture-specific:

- Initiation-set violation increases when a predecessor terminates outside the next option's learned support.
- Termination drift compounds over chains.
- Ambitious subgoals can receive high proxy scores while being outside reliable option spans.
- Candidate-budget growth increases the chance of selecting a rare high-proxy, low-executability chain.

The repair, Handoff-Calibrated Sieve, is boundary-specific: it does not need hidden execution labels, only public evidence about handoff surprise, initiation margins, and termination uncertainty.

## Reviewer Attack Surface

- The simulator is controlled and low-dimensional.
- Boundary diagnostics are hand-designed.
- The repair may look obvious unless the paper shows that proxy-tail planning specifically selects the unsafe handoff tail.
- The rank-tail calibration law is exact but modest.
- Claims must avoid implying real robot benchmark superiority.

## Most Worth Pursuing

Position the work as a mechanism paper with a falsifiable handoff audit, rank-tail calibration, and a repair that defines what real systems should estimate. The strongest next experiment would plug learned initiation/termination estimators into a real skill-chaining benchmark.
