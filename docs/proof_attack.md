# Proof Attack

## Proposition Under Test

For a finite proposal population of option plans `P = {(S_i, U_i)}_{i=1}^M`, where `S_i` is a proxy score and `U_i` is true utility, draw `N` candidates independently and uniformly with replacement from `P`. Select the candidate with the largest proxy score. If proxy scores are sorted increasingly with deterministic tie-breaking, then:

```text
E[U_selected(N)] = sum_{r=1}^M U_(r) * [(r/M)^N - ((r-1)/M)^N]
```

where `U_(r)` is the true utility attached to the plan at proxy rank `r`.

## Proof Sketch

The item at rank `r` is selected exactly when all `N` samples have rank at most `r` and at least one sample has rank exactly `r`. Since samples are uniform with replacement:

```text
P(max rank = r) = (r/M)^N - ((r-1)/M)^N.
```

Linearity of expectation gives the result.

## Attack 1: Ties

If proxy ties exist, the rank formula needs a tie policy. The implementation uses continuous proxy noise and stable sorting. The theorem in the paper states deterministic tie-breaking rather than pretending ties cannot happen.

## Attack 2: Without Replacement

The formula is for with-replacement draws from a proposal distribution. A without-replacement candidate set has a hypergeometric rank law. The experiments generate independent candidates, so the with-replacement version is the correct abstraction.

## Attack 3: Adaptive Planners

The law does not cover planners that adapt proposal distributions after seeing candidates. The paper states the theorem for fixed proposal populations and uses it as a diagnostic, not as a universal theorem for all hierarchical planning.

## Attack 4: Does the Law Prove Degradation?

No. The law explains how selection concentrates on high proxy ranks. Degradation requires the empirical or assumed condition that high proxy ranks have lower true utility because of boundary miscalibration. The experiments test that condition directly.

## Attack 5: Repair Leakage

The repair must not use hidden true executability or true utility. The implementation test `test_boundary_sieve_does_not_reference_hidden_true_labels` inspects the sieve methods, and the method uses only public diagnostics.

## Numerical Check

`python -m bonoptions.experiments.run_all` writes `results/finite_n_validation.csv`. The claim audit requires the Monte Carlo mean to match the finite-N law with mean absolute error below `0.055`; the current generated audit passes.
