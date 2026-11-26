from __future__ import annotations

import re
import sys
from datetime import date
from math import erf, sqrt
from pathlib import Path
from typing import Annotated, TypedDict, cast

import httpx
import joblib
import nflreadpy as nfl
import polars as pl
from fastapi import FastAPI, HTTPException, Query
from nflreadpy.config import get_config, update_config
from nflreadpy.utils_date import get_current_season
from pydantic import BaseModel, Field, ValidationError, computed_field
from sqlalchemy import text
from sqlalchemy.engine import Engine


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SRC_ROOT = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from src.db.database import engine
    from src.model.old_predict import predict_wp_dictionary
except ImportError:  # pragma: no cover - fallback for direct script execution
    from db.database import engine
    from model.old_predict import predict_wp_dictionary
from model.old_predict import predict_wp_dictionary
from model.get_live_state import get_live_state
from model.predict_play import PLAY_TYPES, predict_wp_by_play


app = FastAPI()

# A full season of play-by-play data is too large to retain for every season visited.
if "cache_mode" not in get_config().model_fields_set:
    update_config(cache_mode="filesystem")

old_model = joblib.load(SRC_ROOT / "model" / "old_model.pkl")

model = joblib.load(SRC_ROOT / "model" / "wp_play_model.joblib")

ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

class oldGameState(BaseModel):
    
    game_seconds_remaining: int = Field(ge = 0, le = 3600)
    down: int = Field(ge = 0, le = 4)
    ydstogo: int = Field(ge = 1)
    home_yardline_100: int = Field(ge = 0, le = 100)
    
class GameState(BaseModel):

    game_seconds_remaining: int = Field(ge = 0, le = 3600)
    #half_seconds_remaining: int = Field(ge=0, le=1800)
    down: int = Field(ge = 0, le = 4)
    ydstogo: int = Field(ge = 1)
    yardline_100: int = Field(ge = 0, le = 100)
    score_differential: int
    posteam_timeouts_remaining: int = Field(ge=0, le=3)
    defteam_timeouts_remaining: int = Field(ge=0, le=3)
    posteam_is_home: bool
    posteam_spread: float
    
    @computed_field
    @property
    def half_seconds_remaining(self) -> int:
        if self.game_seconds_remaining > 1800:
            return self.game_seconds_remaining - 1800

        return self.game_seconds_remaining

@app.get("/")
def root():
    return {"message": "NFL Win Probability API is running"}

# old prediction for first prototype
@app.post("/predict/old")
def oldpredict(game_state : oldGameState):
    game_dict = game_state.model_dump()
        
    return predict_wp_dictionary(old_model, game_dict);

# manual user input prediction on model in next_play_model
@app.post("/predict")
def predict(game_state : GameState):
    game_dict = game_state.model_dump()
        
    return predict_wp_by_play(model, game_dict).to_dict()

# live game input prediction on model in next_play_model
@app.post("/games/{event_id}/predict")
def predict_live_game(event_id: str):
    
    try:
        game_state = import_live_game(event_id)
    except:
        raise HTTPException(status_code=404, detail=str("Invalid game ID. Please select a valid NFL game."))
    game_dict = game_state.model_dump()
    predictions = predict_wp_by_play(model,game_dict)
    
    return predictions.to_dict()

# import live game state and turns it into game state model ready for model
@app.get("/games/{event_id}/state")
def import_live_game(event_id: str):

    try:
        result = get_live_state(event_id)
    except:
        raise HTTPException(status_code=404, detail=str("Invalid game ID. Please select a valid NFL game."))

    if result["state"] is None:
        raise HTTPException(
            status_code=422,
            detail=result["problems"]
        )

    return GameState.model_validate(result["state"])

# get live id and team names 
@app.get("/live_games")
def get_live_games():
    response = httpx.get(ESPN_URL)
    response.raise_for_status()
    
    games = response.json()["events"]
    
    live_games = [
        {
            "id": game["id"],
            "name": game["name"],
            "away_team": next(
                {
                    "abbreviation": competitor["team"]["abbreviation"],
                    "name": competitor["team"]["displayName"],
                }
                for competitor in game["competitions"][0]["competitors"]
                if competitor["homeAway"] == "away"
            ),
            "home_team": next(
                {
                    "abbreviation": competitor["team"]["abbreviation"],
                    "name": competitor["team"]["displayName"],
                }
                for competitor in game["competitions"][0]["competitors"]
                if competitor["homeAway"] == "home"
            ),
        }
        for game in games
        if game["status"]["type"]["state"] == "in"
    ]
    
    return live_games


class PastGame(BaseModel):
    game_id: str
    week: int
    gameday: date
    away_team: str
    home_team: str


class PastPlay(BaseModel):
    play_id: int
    quarter: int
    clock: str
    away_score: int
    home_score: int
    state: GameState


class MatchupTeamStats(BaseModel):
    team: str
    games: int
    wins: int
    losses: int
    ties: int
    points_for: int
    points_against: int
    points_for_per_game: float
    points_against_per_game: float
    win_pct: float
    home_wins: int
    home_losses: int
    home_ties: int
    away_wins: int
    away_losses: int
    away_ties: int


class MatchupPrediction(BaseModel):
    season: int
    games_sampled: int
    team_a: MatchupTeamStats
    team_b: MatchupTeamStats
    home_team: str
    probability_a: float
    probability_b: float
    expected_points_a: float
    expected_points_b: float
    expected_margin_a: float
    home_field_advantage: float
    margin_std_dev: float


class TeamSeasonRecord(TypedDict):
    games: int
    wins: int
    losses: int
    ties: int
    points_for: int
    points_against: int
    home_wins: int
    home_losses: int
    home_ties: int
    away_wins: int
    away_losses: int
    away_ties: int


SCHEDULE_TEAM_ALIASES = {"LAR": "LA"}
DEFAULT_MARGIN_STD_DEV = 13.5


def _new_team_season_record() -> TeamSeasonRecord:
    return {
        "games": 0,
        "wins": 0,
        "losses": 0,
        "ties": 0,
        "points_for": 0,
        "points_against": 0,
        "home_wins": 0,
        "home_losses": 0,
        "home_ties": 0,
        "away_wins": 0,
        "away_losses": 0,
        "away_ties": 0,
    }


def _matchup_team_stats(team: str, record: TeamSeasonRecord) -> MatchupTeamStats:
    games = record["games"]
    return MatchupTeamStats(
        team=team,
        games=games,
        wins=record["wins"],
        losses=record["losses"],
        ties=record["ties"],
        points_for=record["points_for"],
        points_against=record["points_against"],
        points_for_per_game=record["points_for"] / games,
        points_against_per_game=record["points_against"] / games,
        win_pct=(record["wins"] + record["ties"] / 2) / games,
        home_wins=record["home_wins"],
        home_losses=record["home_losses"],
        home_ties=record["home_ties"],
        away_wins=record["away_wins"],
        away_losses=record["away_losses"],
        away_ties=record["away_ties"],
    )


def load_completed_schedule(season: int) -> pl.DataFrame:
    try:
        schedule = nfl.load_schedules(season)
    except (ConnectionError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Could not load the NFL schedule.") from exc

    return schedule.filter(pl.col("home_score").is_not_null() & pl.col("away_score").is_not_null())


@app.get("/past_games")
def get_past_games(season: Annotated[int, Query(ge=1999)]) -> list[PastGame]:
    completed = (
        load_completed_schedule(season)
        .select(*PastGame.model_fields)
        .sort(["week", "gameday", "game_id"], descending=[True, False, False])
    )
    return [PastGame.model_validate(row) for row in completed.iter_rows(named=True)]


@app.get("/past_games/{game_id}/plays")
def get_past_plays(game_id: str) -> list[PastPlay]:
    if re.fullmatch(r"[0-9]{4}_[0-9]{2}_[A-Z]{2,3}_[A-Z]{2,3}", game_id) is None:
        raise HTTPException(status_code=404, detail="Completed game not found.")

    season = int(game_id[:4])
    if season < 1999 or (
        load_completed_schedule(season).filter(pl.col("game_id") == game_id).is_empty()
    ):
        raise HTTPException(status_code=404, detail="Completed game not found.")

    if season > get_current_season():
        return []

    try:
        pbp = nfl.load_pbp(season)
    except (ConnectionError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Could not load NFL play-by-play data.") from exc

    # The possessing and defending teams' scores are recorded before the play.
    home_has_ball = pl.col("posteam") == pl.col("home_team")
    scrimmage_plays = [*PLAY_TYPES, "qb_kneel", "qb_spike"]
    plays = (
        pbp.filter(
            (pl.col("game_id") == game_id)
            & pl.col("play_type").is_in(scrimmage_plays)
            & pl.col("down").is_between(1, 4)
        )
        .with_columns(
            home_has_ball.alias("posteam_is_home"),
            pl.when(home_has_ball)
            .then(pl.col("posteam_score"))
            .otherwise(pl.col("defteam_score"))
            .alias("home_score"),
            pl.when(home_has_ball)
            .then(pl.col("defteam_score"))
            .otherwise(pl.col("posteam_score"))
            .alias("away_score"),
        )
        .select("play_id", "qtr", "time", "home_score", "away_score", *GameState.model_fields)
        .sort("play_id")
    )

    replay: list[PastPlay] = []
    for row in plays.iter_rows(named=True):
        try:
            play = PastPlay(
                play_id=row["play_id"],
                quarter=row["qtr"],
                clock=row["time"],
                home_score=row["home_score"],
                away_score=row["away_score"],
                state=GameState.model_validate(row),
            )
        except ValidationError:
            # Some recorded plays lack a usable pre-snap situation.
            continue
        replay.append(play)
    return replay


@app.get("/predict/matchup")
def predict_matchup(
    team_a: Annotated[str, Query(min_length=2, max_length=3, pattern=r"^[A-Z]{2,3}$")],
    team_b: Annotated[str, Query(min_length=2, max_length=3, pattern=r"^[A-Z]{2,3}$")],
    season: Annotated[int, Query(ge=1999)],
    home_team: Annotated[str, Query(min_length=2, max_length=3, pattern=r"^[A-Z]{2,3}$")],
) -> MatchupPrediction:
    if team_a == team_b:
        raise HTTPException(status_code=422, detail="Choose two different teams.")
    if home_team not in (team_a, team_b):
        raise HTTPException(status_code=422, detail="The home team must be one of the selected teams.")

    completed = load_completed_schedule(season).filter(pl.col("game_type") == "REG")
    if completed.is_empty():
        raise HTTPException(
            status_code=422,
            detail=f"No completed regular-season games are available for {season}.",
        )

    records: dict[str, TeamSeasonRecord] = {}
    game_margins: list[float] = []
    for game in completed.iter_rows(named=True):
        home_code = game["home_team"]
        away_code = game["away_team"]
        home_score = int(game["home_score"])
        away_score = int(game["away_score"])
        game_margins.append(float(home_score - away_score))

        home_record = records.setdefault(home_code, _new_team_season_record())
        away_record = records.setdefault(away_code, _new_team_season_record())
        home_record["games"] += 1
        away_record["games"] += 1
        home_record["points_for"] += home_score
        home_record["points_against"] += away_score
        away_record["points_for"] += away_score
        away_record["points_against"] += home_score

        if home_score == away_score:
            home_record["ties"] += 1
            home_record["home_ties"] += 1
            away_record["ties"] += 1
            away_record["away_ties"] += 1
        elif home_score > away_score:
            home_record["wins"] += 1
            home_record["home_wins"] += 1
            away_record["losses"] += 1
            away_record["away_losses"] += 1
        else:
            away_record["wins"] += 1
            away_record["away_wins"] += 1
            home_record["losses"] += 1
            home_record["home_losses"] += 1

    schedule_team_a = SCHEDULE_TEAM_ALIASES.get(team_a, team_a)
    schedule_team_b = SCHEDULE_TEAM_ALIASES.get(team_b, team_b)
    if schedule_team_a not in records or schedule_team_b not in records:
        raise HTTPException(
            status_code=422,
            detail=f"Both teams need at least one completed regular-season game in {season}.",
        )

    stats_a = _matchup_team_stats(team_a, records[schedule_team_a])
    stats_b = _matchup_team_stats(team_b, records[schedule_team_b])
    home_advantage = sum(game_margins) / len(game_margins)
    margin_std_dev = (
        sqrt(sum((margin - home_advantage) ** 2 for margin in game_margins) / len(game_margins))
        if len(game_margins) > 1
        else DEFAULT_MARGIN_STD_DEV
    )
    if margin_std_dev == 0:
        margin_std_dev = DEFAULT_MARGIN_STD_DEV

    neutral_points_a = (stats_a.points_for_per_game + stats_b.points_against_per_game) / 2
    neutral_points_b = (stats_b.points_for_per_game + stats_a.points_against_per_game) / 2
    home_adjustment = home_advantage / 2
    expected_points_a = neutral_points_a + (home_adjustment if home_team == team_a else -home_adjustment)
    expected_points_b = neutral_points_b + (home_adjustment if home_team == team_b else -home_adjustment)
    expected_margin_a = expected_points_a - expected_points_b
    probability_a = 0.5 * (1 + erf(expected_margin_a / (margin_std_dev * sqrt(2))))
    probability_a_pct = round(probability_a * 100, 1)

    return MatchupPrediction(
        season=season,
        games_sampled=len(game_margins),
        team_a=stats_a,
        team_b=stats_b,
        home_team=home_team,
        probability_a=probability_a_pct,
        probability_b=round(100 - probability_a_pct, 1),
        expected_points_a=round(expected_points_a, 1),
        expected_points_b=round(expected_points_b, 1),
        expected_margin_a=round(expected_margin_a, 1),
        home_field_advantage=round(home_advantage, 1),
        margin_std_dev=round(margin_std_dev, 1),
    )


# get standings data, the format is the same of Google NFL standings widget
@app.get("/standings")
def get_standings():
    if engine is None:
        return []

    with cast(Engine, engine).connect() as conn:
        result = conn.execute(
            text("SELECT * FROM standings")
        )

    return [dict(row) for row in result.mappings()]

game_state = GameState(
    game_seconds_remaining=2400,
    down=2,
    ydstogo=6,
    yardline_100=45,
    score_differential=2,
    posteam_timeouts_remaining=3,
    defteam_timeouts_remaining=3,
    posteam_is_home=True,
    posteam_spread=3.0
)

game_dict = game_state.model_dump()

print(game_dict)