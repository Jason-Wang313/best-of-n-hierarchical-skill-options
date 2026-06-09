from bonoptions.experiments.common import finite_n_validation, run_selection_sweep


def test_smoke_sweep_contains_raw_and_repair() -> None:
    df = run_selection_sweep(
        ns=[1, 4],
        seeds=range(2),
        horizon=3,
        mode="miscalibrated",
        dataset="test",
        include_repair=True,
    )
    assert set(df["selector"]) == {"raw_bon", "boundary_sieve"}
    assert set(df["N"]) == {1, 4}


def test_finite_n_validation_is_close_to_monte_carlo() -> None:
    df = finite_n_validation(ns=[1, 4], population_size=300, repetitions=250, seed=5, horizon=3)
    assert float(df["abs_error"].mean()) < 0.18
