from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path
from typing import Annotated, cast

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