from __future__ import annotations

from skill_handoff_audit.taxi_benchmark import (
    canonical_chain,
    evaluate_candidate,
    sample_candidate_chains,
    select_handoff_sieve,
    taxi_initial_states,
)


def test_taxi_canonical_chain_executes_better_than_proxy_trap():
    obs = taxi_initial_states(seed=80, count=1)[0]
    canonical = evaluate_candidate(obs, canonical_chain(obs))
    trap = evaluate_candidate(obs, sample_candidate_chains(obs, n=6, seed=123)[1])

    assert canonical.true_return > trap.true_return
    assert canonical.diagnostics.public_boundary_risk < trap.diagnostics.public_boundary_risk


def test_taxi_handoff_sieve_uses_public_boundary_signal():
    obs = taxi_initial_states(seed=81, count=1)[0]
    candidates = [evaluate_candidate(obs, chain) for chain in sample_candidate_chains(obs, n=12, seed=456)]
    proxy = max(candidates, key=lambda cand: cand.proxy_score)
    selected = select_handoff_sieve(candidates)

    assert selected.true_return >= proxy.true_return
    assert selected.diagnostics.public_boundary_risk <= proxy.diagnostics.public_boundary_risk
