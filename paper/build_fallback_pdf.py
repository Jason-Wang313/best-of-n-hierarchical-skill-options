from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
FINAL = PAPER / "final"


def add_text_page(pdf: PdfPages, title: str, paragraphs: list[str]) -> None:
    fig = plt.figure(figsize=(8.5, 11))
    fig.patch.set_facecolor("white")
    y = 0.94
    fig.text(0.08, y, title, fontsize=18, weight="bold", va="top")
    y -= 0.06
    for paragraph in paragraphs:
        for line in textwrap.wrap(paragraph, width=92):
            fig.text(0.08, y, line, fontsize=10.5, va="top")
            y -= 0.022
            if y < 0.08:
                pdf.savefig(fig)
                plt.close(fig)
                fig = plt.figure(figsize=(8.5, 11))
                fig.patch.set_facecolor("white")
                y = 0.94
        y -= 0.018
    pdf.savefig(fig)
    plt.close(fig)


def add_image_page(pdf: PdfPages, image_path: Path, title: str) -> None:
    fig = plt.figure(figsize=(8.5, 11))
    fig.patch.set_facecolor("white")
    fig.text(0.08, 0.94, title, fontsize=16, weight="bold", va="top")
    if image_path.exists():
        image = plt.imread(image_path)
        ax = fig.add_axes([0.08, 0.18, 0.84, 0.66])
        ax.imshow(image)
        ax.axis("off")
    else:
        fig.text(0.08, 0.82, f"Missing figure: {image_path}", fontsize=11)
    pdf.savefig(fig)
    plt.close(fig)


def main() -> None:
    FINAL.mkdir(parents=True, exist_ok=True)
    out = FINAL / "iclr_submission.pdf"
    paragraphs = [
        "Best-of-N Search Amplifies Option-Boundary Errors in Hierarchical Skill Planning",
        "Anonymous ICLR-style draft fallback. Local LaTeX compilation was unavailable or failed; see paper/final/build_log.md for the exact build status.",
        "Abstract: Hierarchical robot planners compose learned skills, options, or subgoals with a high-level scorer. Best-of-N inference samples many abstract plans and executes the highest proxy-scoring plan. This controlled mechanism study shows that when the proxy is miscalibrated at option boundaries, increasing N can select plans that look better abstractly but are less executable because their initiation sets, termination distributions, and handoffs are unsafe.",
        "Main result: in the generated sweep, raw Best-of-N raises selected proxy score while reducing option-chain executability at high N. Boundary-Calibrated Option Sieve improves large-N true utility using only public boundary diagnostics.",
        "This fallback PDF is intentionally minimal. The full LaTeX source remains in paper/main.tex and uses the official ICLR 2026 style files when a TeX toolchain is available.",
    ]
    with PdfPages(out) as pdf:
        add_text_page(pdf, "Best-of-N Option-Boundary Errors", paragraphs)
        add_image_page(pdf, PAPER / "figures" / "bon_degradation.png", "Raw Best-of-N Degradation")
        add_image_page(pdf, PAPER / "figures" / "repair_comparison.png", "Boundary Sieve Repair")
        add_image_page(pdf, PAPER / "figures" / "finite_n_law.png", "Finite-N Law Validation")
    print(out)


if __name__ == "__main__":
    main()
