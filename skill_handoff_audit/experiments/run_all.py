from __future__ import annotations

import shutil

import pandas as pd

from skill_handoff_audit.experiments.common import (
    FIGURES,
    PAPER_FIGURES,
    RESULTS,
    finite_n_validation,
    plot_controls,
    plot_degradation,
    plot_finite_law,
    plot_repair,
    run_selection_sweep,
    summarize_selection,
)
from skill_handoff_audit.experiments.run_claim_audit import audit_claims


def main() -> None:
    ns = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
    frames = []
    for mode in ["miscalibrated", "calibrated", "oracle", "random", "anti_correlated"]:
        frames.append(
            run_selection_sweep(
                ns=ns,
                seeds=range(12),
                horizon=4,
                mode=mode,
                dataset="selection",
                include_repair=(mode == "miscalibrated"),
            )
        )

    stress_frames = []
    for horizon in [2, 4, 6, 8]:
        stress_frames.append(
            run_selection_sweep(
                ns=[16, 128, 512],
                seeds=range(8),
                horizon=horizon,
                mode="miscalibrated",
                dataset="horizon_stress",
                include_repair=True,
            )
        )

    df = pd.concat(frames + stress_frames, ignore_index=True)
    df.to_csv(RESULTS / "all_selection.csv", index=False)
    summarize_selection(df).to_csv(RESULTS / "tables" / "selection_summary.csv", index=False)

    finite = finite_n_validation(ns=ns, population_size=1400, repetitions=650, seed=123)
    finite.to_csv(RESULTS / "finite_n_validation.csv", index=False)

    figure_paths = [
        FIGURES / "handoff_tail_degradation.png",
        FIGURES / "repair_comparison.png",
        FIGURES / "controls.png",
        FIGURES / "rank_tail_calibration.png",
    ]
    plot_degradation(df, figure_paths[0])
    plot_repair(df, figure_paths[1])
    plot_controls(df, figure_paths[2])
    plot_finite_law(finite, figure_paths[3])
    for path in figure_paths:
        shutil.copy2(path, PAPER_FIGURES / path.name)

    audit_claims(selection_path=RESULTS / "all_selection.csv", finite_path=RESULTS / "finite_n_validation.csv")
    print(f"wrote {RESULTS / 'all_selection.csv'}")
    print(f"wrote {RESULTS / 'finite_n_validation.csv'}")
    print(f"wrote figures under {FIGURES}")


if __name__ == "__main__":
    main()
