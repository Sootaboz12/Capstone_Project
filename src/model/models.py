"""Estimate home win probability by counting similar historical situations.

pbp means play-by-play data: each row describes a play or game event.
Fields used here:
    game_id: identifies the game.
    season: NFL season year; used to separate counting from evaluation.
    play_id: identifies a play within a game; used to order the plays.
    play: 1 marks a play event, rather than a bookkeeping row.
    qtr: quarter number; 1-4 are regulation, 5 is overtime.
    posteam_type: "home" or "away", whichever team has possession.
    play_type: what the team with possession did ("run" or "pass"). Runs include scrambles; passes include sacks.
    score_differential: possession team's score minus opponent's, before the play.
    game_seconds_remaining: seconds left in the game, not just the quarter.
    result: FINAL home score minus away score; positive means home won.

We create score_diff (home team's current lead), time_bucket (whole minutes
remaining), and home_win (1 if home eventually won, otherwise 0).

This version excludes tied games and overtime plays. Missing groups use the
historical home win rate. Small groups can still give unreliable estimates.
It also assumes historical patterns are useful for predicting future games.
Run/pass comparisons describe historical outcomes, not the causal effect of
choosing a play.
"""

from typing import Literal, TypedDict

import nflreadpy as nfl
import pandas as pd


class GameState(TypedDict):
    score_diff: int
    game_seconds_remaining: int
    posteam_type: Literal["home", "away"]
    play_type: Literal["run", "pass"]


# Only score, time, possession, and play type determine which situations match.
# Down, field position, yards to go, timeouts, and team strength are ignored.
GROUP_COLUMNS: list[str] = ["score_diff", "time_bucket", "posteam_type", "play_type"]


def prepare_plays(pbp: pd.DataFrame) -> pd.DataFrame:
    # Keep plays from the normal four quarters (regulation).
    # Exclude overtime: its rules and clock differ, so it needs separate groups.
    # Regulation plays from games that went into overtime still count,
    # using the eventual winner of the whole game.
    # Exclude tied games: our labels only represent a home win or an away win.
    plays: pd.DataFrame = pbp.loc[
        (pbp["play"] == 1)
        & (pbp["result"] != 0)
        & (pbp["qtr"] <= 4)
        & pbp["play_type"].isin(["run", "pass"])
    ].copy()

    # The final result tells us whether the home team eventually won.
    plays["home_win"] = (plays["result"] > 0).astype(int)

    # score_differential is the possession team's lead before the play.
    # Flip it when the away team has the ball to get the home team's lead.
    plays["score_diff"] = plays["score_differential"]
    away_has_ball: pd.Series = plays["posteam_type"] == "away"
    plays.loc[away_has_ball, "score_diff"] *= -1

    # Put time into one-minute groups: 300 through 359 seconds become 5.
    # Seconds within a group are treated alike; predictions can jump at boundaries.
    plays["time_bucket"] = plays["game_seconds_remaining"] // 60

    assert isinstance(plays, pd.DataFrame)
    return plays


def build_counts(plays: pd.DataFrame) -> pd.DataFrame:
    # Count each training game once per group, using its first matching play.
    # This answers: "Among games that reached this situation and used this
    # play type, how often did the home team win?"
    plays = plays.sort_values(["game_id", "play_id"])
    plays = plays.drop_duplicates(subset=["game_id", *GROUP_COLUMNS])

    # Count wins and games for each situation and play type.
    counts: pd.DataFrame = plays.groupby(GROUP_COLUMNS, as_index=False).agg(
        home_wins=("home_win", "sum"),
        games=("home_win", "count"),
    )
    # Small groups give less reliable estimates; we do not handle that yet.
    counts["home_win_rate"] = counts["home_wins"] / counts["games"]
    return counts


def predict_win_rate(
    counts: pd.DataFrame, game_state: GameState, fallback_rate: float
) -> float:
    # Find the historical group that matches this situation.
    time_bucket: int = game_state["game_seconds_remaining"] // 60
    matching_group: pd.DataFrame = counts.loc[
        (counts["score_diff"] == game_state["score_diff"])
        & (counts["time_bucket"] == time_bucket)
        & (counts["posteam_type"] == game_state["posteam_type"])
        & (counts["play_type"] == game_state["play_type"])
    ]

    # An unseen situation uses the training games' overall home win rate.
    if matching_group.empty:
        return fallback_rate

    # Its fraction of home wins is our prediction.
    return float(matching_group.iloc[0]["home_win_rate"])


def evaluate(
    counts: pd.DataFrame, validation: pd.DataFrame, fallback_rate: float
) -> None:
    # Look up a prediction for every validation situation in one table join.
    results: pd.DataFrame = validation.merge(
        counts[GROUP_COLUMNS + ["home_win_rate"]],
        on=GROUP_COLUMNS,
        how="left",
    )
    missing_group: pd.Series = results["home_win_rate"].isna()
    results["prediction"] = results["home_win_rate"].fillna(fallback_rate)

    # Lower Brier score means smaller probability errors.
    # Compare with always predicting the overall training home win rate.
    brier: float = float(((results["prediction"] - results["home_win"]) ** 2).mean())
    baseline_brier: float = float(((fallback_rate - results["home_win"]) ** 2).mean())
    print(f"Counting Brier score: {brier:.4f}")
    print(f"Baseline Brier score: {baseline_brier:.4f}")
    print(f"Situations using fallback: {missing_group.mean():.1%}")

    # Calibration: compare average predictions with actual win rates.
    # These probability bands are for checking predictions, not matching plays.
    results["probability_band"] = pd.cut(
        results["prediction"],
        bins=[percent / 100 for percent in range(0, 101, 10)],
        labels=[f"{percent}-{percent + 10}%" for percent in range(0, 100, 10)],
        include_lowest=True,
    )
    # Answers: "Among evaluated situations where this play type occurred and
    # our prediction fell into this probability band, how closely did the
    # average prediction match the actual home win rate?"
    # The usefulness is asymmetric:
    # - A large mismatch reveals a problem worth investigating.
    # - A close match does not establish accuracy within individual situations, because errors can cancel.
    calibration: pd.DataFrame = results.groupby(
        ["play_type", "probability_band"], observed=True
    ).agg(
        average_prediction=("prediction", "mean"),
        actual_win_rate=("home_win", "mean"),
        situations=("home_win", "count"),
    )
    print("Calibration by play type (rates are between 0 and 1):")
    print(calibration.round(3).to_string())


if __name__ == "__main__":
    # Use older seasons for counting and a later season to check predictions.
    # No 2024 game contributes to the counts or fallback rate.
    pbp: pd.DataFrame = nfl.load_pbp(seasons=[2022, 2023, 2024]).to_pandas()
    plays: pd.DataFrame = prepare_plays(pbp)
    train: pd.DataFrame = plays.loc[plays["season"] < 2024].copy()
    validation: pd.DataFrame = plays.loc[plays["season"] == 2024].copy()
    counts: pd.DataFrame = build_counts(train)

    # Count each training game once when calculating the fallback.
    training_games: pd.DataFrame = train.drop_duplicates(subset="game_id")
    fallback_rate: float = float(training_games["home_win"].mean())

    # Show how much history supports the groups, then check later games.
    print("Games supporting each group:")
    print(counts["games"].agg(["min", "median", "max"]).to_string())
    evaluate(counts, validation, fallback_rate)

    # Example: home leads by 3, has the ball, and 5 minutes remain.
    game_state: GameState = {
        "score_diff": 3,
        "game_seconds_remaining": 300,
        "posteam_type": "home",
        "play_type": "run",
    }
    play_types: list[Literal["run", "pass"]] = ["run", "pass"]
    for play_type in play_types:
        game_state["play_type"] = play_type
        probability: float = predict_win_rate(counts, game_state, fallback_rate)
        print(f"Home win probability with {play_type}: {probability:.1%}")
