from __future__ import annotations

from skill_handoff_audit.experiments.common import (
    FIGURES,
    RESULTS,
    finite_n_validation,
    plot_degradation,
    plot_finite_law,
    plot_repair,
    run_selection_sweep,
)


def main() -> None:
    ns = [1, 4, 16, 64, 256]
    df = run_selection_sweep(
        ns=ns,
        seeds=range(6),
        horizon=4,
        mode="miscalibrated",
        dataset="selection",
        include_repair=True,
    )
    out_csv = RESULTS / "smoke_selection.csv"
    df.to_csv(out_csv, index=False)

    finite = finite_n_validation(ns=ns, population_size=900, repetitions=500, seed=14)
    finite.to_csv(RESULTS / "smoke_finite_n.csv", index=False)

    plot_degradation(df, FIGURES / "smoke_handoff_tail.png")
    plot_repair(df, FIGURES / "smoke_repair.png")
    plot_finite_law(finite, FIGURES / "smoke_rank_tail_calibration.png")
    print(f"wrote {out_csv}")
    print(f"wrote {RESULTS / 'smoke_finite_n.csv'}")


if __name__ == "__main__":
    main()
