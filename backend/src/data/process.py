import nflreadpy as nfl
import polars as pl


def process_pbp():
    pbp = nfl.load_pbp(seasons=True)

    # filtering for only play events
    pbp_plays = pbp.filter( 
        pl.col("play") == 1.0
    )

    pbp_plays = pbp_plays.select([
        "game_id",
        "play_id",
        "season",
        "week",

        "home_team",
        "away_team",
        "posteam",
        "defteam",

        "posteam_type",
        "total_home_score",
        "total_away_score",
        "qtr",
        "game_seconds_remaining",
        "down",
        "ydstogo",
        "yardline_100",
        "goal_to_go",
        "posteam_timeouts_remaining",
        "defteam_timeouts_remaining",
        "score_differential",

        "play_type",

        "home_score",
        "away_score"
    ])

    #  adding col that indicates if team with posession wins the game
    pbp_plays = pbp_plays.with_columns(
        pl.when(pl.col("posteam_type") == "home")
        .then(
            (pl.col("home_score") > pl.col("away_score")).cast(pl.Int8)
        )
        .otherwise(
            (pl.col("away_score") > pl.col("home_score")).cast(pl.Int8)
        )
        .alias("posteam_won")
    )

    return pbp_plays