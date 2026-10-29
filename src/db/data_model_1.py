import nflreadpy as nfl
import polars as pl


def process_pbp():
    pbp = nfl.load_pbp(seasons=True)

    # filtering for only play events
    pbp_plays = pbp.filter( 
        pl.col("play") == 1.0
    )
    
    pbp_plays = pbp_plays.with_columns(
    (pl.col("total_home_score") - pl.col("total_away_score")).alias("score_diff")
    )
    
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
        "score_diff",
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
        "result",
        "home_score",
        "away_score"
    ])

    return pbp_plays # master dataframe with identification features for debugging and adding more features


def create_model_df(): # dataframe for model
    pbp = nfl.load_pbp(seasons=True)

    # filtering for only play events
    pbp_plays = pbp.filter( 
        pl.col("play") == 1.0
    )
    
    pbp_plays = pbp_plays.with_columns(
        (pl.col("total_home_score") - pl.col("total_away_score")).alias("score_diff")
    )
    
    pbp_plays = pbp_plays.with_columns(
        pl.when(pl.col("posteam_type") == "home")
        .then(pl.col("yardline_100"))
        .otherwise(100 - pl.col("yardline_100"))
        .alias("home_yardline_100")
    )

    return pbp_plays.select([
        "game_id",
        "season",
        
        "score_diff",
        
        "qtr",
        "game_seconds_remaining",
        "down",
        "ydstogo",
        "home_yardline_100",
        "goal_to_go",
        "posteam_timeouts_remaining",
        "defteam_timeouts_remaining",
        
        "result",
])


def main(): 

# using main() to debug

    pbp = process_pbp() 
    
    # checking to see result, score_diff
    # pbp_plays = (pbp
    # .filter(pl.col("game_id") == "2025_22_SEA_NE")
    # .select(["score_diff", "result","home_team","home_score","away_team","away_score"])
    # )
    
    print(
        pbp.select(
            pl.col("ydstogo").min().alias("min"),
            pl.col("ydstogo").max().alias("max"),
            pl.col("ydstogo").null_count().alias("nulls"),
        )
    )
if __name__ == "__main__":
    main()