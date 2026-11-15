"""Reproduce Google's four threshold plots for three NFL situation features.

Reads historical data only; never imports, trains, or runs the WP model.
Reference: https://developers.google.com/machine-learning/decision-forests/binary-classification
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy.typing import NDArray


FEATURE = "score_differential"
FEATURE_LABELS: dict[str, tuple[str, str, str]] = {
    "score_differential": ("Score differential", "points", "score"),
    "yardline_100": ("Yards to opponent's end zone", "yards", "yards"),
    "ydstogo": ("Yards to go", "yards", "yards to go"),
}
REQUIRED = ["down", "ydstogo", "yardline_100", FEATURE, "game_seconds_remaining"]


def entropy(p: NDArray[np.float64]) -> NDArray[np.float64]:
    """Binary Shannon entropy in bits; pure groups have zero entropy."""
    result = np.zeros_like(p, dtype=float)
    mixed = (p > 0) & (p < 1)
    q = p[mixed]
    result[mixed] = -q * np.log2(q) - (1 - q) * np.log2(1 - q)
    return result


def split_curve(
    x: NDArray[np.float64], y: NDArray[np.int64]
) -> pd.DataFrame:
    """Scan every midpoint between distinct values, as in Google's exact splitter.

    F is x < threshold; T is x >= threshold. Every nonempty split is eligible.
    Sorting and cumulative sums avoid repeatedly scanning the observations.
    """
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Need at least two paired observations.")
    if not np.isfinite(x).all() or not np.isin(y, [0, 1]).all():
        raise ValueError("Features must be finite and labels must be 0 or 1.")
    order = np.argsort(x)
    values, labels = x[order], y[order]
    positions = np.flatnonzero(values[:-1] != values[1:])
    if not len(positions):
        raise ValueError("Need at least two distinct feature values.")
    thresholds = values[positions] / 2 + values[positions + 1] / 2
    n_f = positions + 1
    n_t = len(y) - n_f
    wins_f = np.cumsum(labels)[positions]
    p_f = wins_f / n_f
    p_t = (labels.sum() - wins_f) / n_t
    h_f, h_t = entropy(p_f), entropy(p_t)
    p_d = float(y.mean())
    h_d = float(entropy(np.array([p_d]))[0])
    gain = h_d - (n_f * h_f + n_t * h_t) / len(y)
    return pd.DataFrame({
        "threshold": thresholds, "n_f": n_f, "n_t": n_t,
        "p_f": p_f, "p_t": p_t, "p_d": p_d,
        "h_f": h_f, "h_t": h_t, "h_d": h_d,
        "information_gain": gain,
    })


def prepare_plays(path: Path) -> pd.DataFrame:
    """Use next_play_model_testing's play filters and possession-team outcome."""
    columns = ["season", "game_id", "play_type", "posteam", "home_team", "result", *REQUIRED]
    pbp = pd.read_parquet(path, columns=columns)
    plays = pbp.loc[
        pbp["play_type"].isin(["run", "pass", "punt", "field_goal"])
        & pbp["posteam"].notna()
        & pbp["result"].notna()
        & (pbp["result"] != 0)
        & pbp["season"].between(2006, 2024)
    ].dropna(subset=REQUIRED).copy()
    pos_result = np.where(
        plays["posteam"] == plays["home_team"], plays["result"], -plays["result"]
    )
    plays["posteam_win"] = (pos_result > 0).astype(int)
    if plays.empty:
        raise ValueError("No eligible training-season plays in this file.")
    return plays


def draw(
    plays: pd.DataFrame, curve: pd.DataFrame, output: Path, feature: str = FEATURE
) -> None:
    """Match Figure 11: histogram, label ratios, entropy, information gain."""
    title, unit, short_label = FEATURE_LABELS[feature]
    best = curve.loc[curve["information_gain"].idxmax()]
    fig, axes = plt.subplots(4, 1, figsize=(10, 11))
    fig.subplots_adjust(left=0.12, right=0.97, top=0.88, bottom=0.14, hspace=0.42)
    seasons = sorted(plays["season"].unique())
    season_label = ", ".join(str(int(s)) for s in seasons)
    fig.suptitle(f"{title}: finding a split", fontsize=17, y=0.98)
    fig.text(0.5, 0.945,
             f"NFL {season_label} | {len(plays):,} plays | {plays['game_id'].nunique():,} games",
             ha="center", fontsize=11)
    fig.text(0.5, 0.919,
             "Positive label = possession team eventually wins; each play is one observation",
             ha="center", fontsize=10)
    x = plays[feature].to_numpy(dtype=float)
    bins = np.arange(x.min() - 0.5, x.max() + 1.5, 1)
    axes[0].hist(x, bins=bins, color="#0878a5")
    axes[0].set_ylabel("Frequency")
    t = curve["threshold"]
    for ax, prefix in [(axes[1], "p"), (axes[2], "h")]:
        ax.plot(t, curve[f"{prefix}_f"], label=f"F: {short_label} < t", color="#1f77b4")
        ax.plot(t, curve[f"{prefix}_t"], label=f"T: {short_label} ≥ t", color="#ff7f0e")
        ax.plot(t, curve[f"{prefix}_d"], label="D: all plays", color="#999999")
        ax.set_ylim(-0.03, 1.05)
        ax.legend(loc="best", fontsize=9)
    axes[1].set_ylabel("Fraction of wins")
    axes[2].set_ylabel("Entropy (bits)")
    axes[3].plot(t, curve["information_gain"], color="#1f77b4")
    axes[3].axvline(best["threshold"], color="#1f77b4", linestyle="--",
                    label=f"Best split: t = {best['threshold']:g}")
    axes[3].set_ylabel("Information gain (bits)")
    axes[3].set_ylim(bottom=0)
    axes[3].legend(loc="upper right", fontsize=9)
    for ax in axes:
        ax.set_xlim(x.min() - 1, x.max() + 1)
        ax.set_xlabel(f"{title} threshold t ({unit})")
        ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.12, 0.038,
             f"Best split: {short_label} ≥ {best['threshold']:g} | gain = {best['information_gain']:.4f} bits\n"
             f"Below: {int(best['n_f']):,} plays, {best['p_f']:.1%} wins   |   "
             f"At/above: {int(best['n_t']):,} plays, {best['p_t']:.1%} wins",
             fontsize=10, linespacing=1.6)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".png"), dpi=160)
    fig.savefig(output.with_suffix(".svg"))
    plt.close(fig)
    # Matplotlib adds trailing spaces inside SVG paths; keep exports diff-clean.
    svg = output.with_suffix(".svg")
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="nflverse PBP parquet file")
    parser.add_argument("--feature", choices=FEATURE_LABELS, default=FEATURE)
    parser.add_argument("--output", type=Path, help="Output path stem; defaults to outputs/<feature>")
    args = parser.parse_args()
    output = args.output or Path(__file__).parent / "outputs" / args.feature
    plays = prepare_plays(args.data)
    curve = split_curve(plays[args.feature].to_numpy(dtype=float),
                        plays["posteam_win"].to_numpy(dtype=np.int64))
    draw(plays, curve, output, args.feature)
    curve.to_csv(output.with_suffix(".csv"), index=False)
    print(curve.loc[curve["information_gain"].idxmax()].to_string())


if __name__ == "__main__":
    main()
