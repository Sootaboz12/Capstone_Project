"""Estimate home win probability by counting similar historical situations.

pbp means play-by-play data: each row describes a play or game event.
Fields used here:
    game_id: identifies the game.
    play_id: identifies a play within a game; used to order the plays.
    play: 1 marks a play event, rather than a bookkeeping row.
    qtr: quarter number; 1-4 are regulation, 5 is overtime.
    posteam_type: "home" or "away", whichever team has possession.
    score_differential: possession team's score minus opponent's, before the play.
    game_seconds_remaining: seconds left in the game, not just the quarter.
    result: FINAL home score minus away score; positive means home won.

We create score_diff (home team's current lead), time_bucket (whole minutes
remaining), and home_win (1 if home eventually won, otherwise 0).

This first version excludes tied games and overtime plays. It assumes a matching group
exists; handling missing groups or small counts can come later.
It also assumes historical patterns are useful for predicting future games.
"""

from typing import Literal, TypedDict

import nflreadpy as nfl
import pandas as pd


class GameState(TypedDict):
    score_diff: int
    game_seconds_remaining: int
    posteam_type: Literal["home", "away"]


def build_counts(pbp: pd.DataFrame) -> pd.DataFrame:
    # Keep plays from the normal four quarters (regulation).
    # Exclude overtime: its rules and clock differ, so it needs separate groups.
    # Regulation plays from games that went into overtime still count,
    # using the eventual winner of the whole game.
    # Exclude tied games: our labels only represent a home win or an away win.
    plays: pd.DataFrame = pbp.loc[
        (pbp["play"] == 1) & (pbp["result"] != 0) & (pbp["qtr"] <= 4)
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
    # Only score, time, and possession determine which situations match.
    # Down, field position, yards to go, timeouts, and team strength are ignored.
    group_columns: list[str] = ["score_diff", "time_bucket", "posteam_type"]

    assert isinstance(plays, pd.DataFrame)

    # Count each game once per group, using its first matching play.
    # Later visits to the same group are ignored so one game cannot dominate it.
    plays = plays.sort_values(["game_id", "play_id"])
    plays = plays.drop_duplicates(subset=["game_id", *group_columns])

    counts: pd.DataFrame = plays.groupby(group_columns, as_index=False).agg(
        home_wins=("home_win", "sum"),
        games=("home_win", "count"),
    )
    # Small groups give less reliable estimates; we do not handle that yet.
    counts["home_win_rate"] = counts["home_wins"] / counts["games"]
    return counts


def predict_win_rate(counts: pd.DataFrame, game_state: GameState) -> float:
    # Find the historical group that matches this situation.
    time_bucket: int = game_state["game_seconds_remaining"] // 60
    matching_group: pd.DataFrame = counts.loc[
        (counts["score_diff"] == game_state["score_diff"])
        & (counts["time_bucket"] == time_bucket)
        & (counts["posteam_type"] == game_state["posteam_type"])
    ]

    # Its fraction of home wins is our prediction.
    # Assumes a match exists; iloc[0] raises an error if the group is empty.
    return float(matching_group.iloc[0]["home_win_rate"])


if __name__ == "__main__":
    # Download historical plays and build the table of counts.
    pbp: pd.DataFrame = nfl.load_pbp(seasons=[2024 - i for i in range(3)]).to_pandas()
    counts: pd.DataFrame = build_counts(pbp)
    print(counts.head().to_string(index=False))

    # Example: home leads by 3, has the ball, and 5 minutes remain.
    game_state: GameState = {
        "score_diff": 3,
        "game_seconds_remaining": 300,
        "posteam_type": "home",
    }
    probability: float = predict_win_rate(counts, game_state)
    print(f"Home win probability: {probability:.1%}")
