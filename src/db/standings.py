import nflreadpy as nfl
import polars as pl

def update_standings():
    
    season = nfl.get_current_season()
    sch = nfl.load_schedules(season)
    teams = nfl.load_teams()
    
    sch = sch.filter(
        (pl.col("game_type") == "REG")
        & pl.col("home_score").is_not_null()
        & pl.col("away_score").is_not_null()
    )
    
    home = sch.select(
        pl.col("home_team").alias("team"),
        (pl.col("home_score") > pl.col("away_score")).cast(pl.Int8).alias("wins"),
        (pl.col("home_score") < pl.col("away_score")).cast(pl.Int8).alias("losses"),
        (pl.col("home_score") == pl.col("away_score")).cast(pl.Int8).alias("ties"),
        (pl.col("home_score").alias("pf")),
        (pl.col("away_score").alias("pa"))
        
    )

    away = sch.select(
        pl.col("away_team").alias("team"),
        (pl.col("away_score") > pl.col("home_score")).cast(pl.Int8).alias("wins"),
        (pl.col("away_score") < pl.col("home_score")).cast(pl.Int8).alias("losses"),
        (pl.col("away_score") == pl.col("home_score")).cast(pl.Int8).alias("ties"),
        (pl.col("away_score").alias("pf")),
        (pl.col("home_score").alias("pa"))
    )
    
    home_records = home.group_by("team").agg(
        pl.sum("wins").alias("home_wins"),
        pl.sum("losses").alias("home_losses"),
        #pl.sum("ties").alias("home_ties")
    )
    
    away_records = away.group_by("team").agg(
        pl.sum("wins").alias("away_wins"),
        pl.sum("losses").alias("away_losses"),
        #pl.sum("ties").alias("away_ties")
    )

    standings = (

        pl.concat([home, away])
        .group_by("team")
        .agg(
            pl.sum("wins"),
            pl.sum("losses"),
            pl.sum("ties"),
            pl.sum("pf"),
            pl.sum("pa")
        )
    )
    
    standings = (standings
    .join(home_records, on="team", how="left")
    .join(away_records, on="team", how="left")
    )
    
    standings = standings.with_columns(
        (
            ((pl.col("wins") + pl.col("ties") / 2.0) / (pl.col("wins") + pl.col("losses") + pl.col("ties"))
            ).round(3).alias("winning_percent")
            
        )
    )
    
    standings = standings.with_columns(
        pl.format(
            "{}-{}",
            pl.col("home_wins"),
            pl.col("home_losses")
        ).alias("home_record")
    )
    
    standings = standings.with_columns(
        pl.format(
            "{}-{}",
            pl.col("away_wins"),
            pl.col("away_losses"),
        ).alias("away_record")
    )
    standings = standings.join(
        teams.select([
            "team_abbr",
            "team_name",
            "team_conf",
            "team_division"
        ]),
        left_on="team",
        right_on="team_abbr",
        how="left"
    )
    
    standings = standings.select(
        "team",
        "team_name",
        "team_conf",
        "team_division",
        "wins",
        "losses",
        "ties",
        "winning_percent",
        pl.exclude(
            "team",
            "team_name",
            "team_conf",
            "team_division",
            "wins",
            "losses",
            "ties",
            "winning_percent",
            "home_wins",
            "home_losses",
            "away_wins",
            "away_losses"
        )
    )  
    pl.Config.set_tbl_cols(-1)
    print(standings.head(10))
    return standings

if __name__ == "__main__":
    update_standings()
    