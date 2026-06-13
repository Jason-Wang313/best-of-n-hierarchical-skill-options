import numpy as np

from skill_handoff_audit.core import OptionWorld, SkillOption


def test_initiation_probability_drops_outside_radius() -> None:
    option = SkillOption(
        option_id="reach",
        init_center=1.0,
        term_center=2.0,
        init_radius=0.5,
        term_sigma=0.1,
        reward=1.0,
        reliable_span=1.2,
    )
    assert option.initiation_probability(1.0) > 0.9
    assert option.initiation_probability(2.0) < 0.1


def test_termination_distribution_tracks_start_mismatch() -> None:
    option = SkillOption(
        option_id="push",
        init_center=0.0,
        term_center=1.0,
        init_radius=0.5,
        term_sigma=0.01,
        reward=1.0,
        reliable_span=1.0,
    )
    rng = np.random.default_rng(0)
    nominal = option.termination_sample(rng, state_mean=0.0)
    shifted = option.termination_sample(rng, state_mean=1.0)
    assert shifted > nominal


def test_world_evaluation_reports_boundary_diagnostics() -> None:
    world = OptionWorld.default(seed=0)
    safe = world.evaluate(["local_0", "local_1", "local_2"])
    risky = world.evaluate(["leap_0", "leap_8", "leap_1"])
    safe_diag = safe[3]
    risky_diag = risky[3]
    assert safe[2] > risky[2]
    assert risky_diag.public_boundary_risk > safe_diag.public_boundary_risk
