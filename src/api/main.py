from __future__ import annotations

import sys
from pathlib import Path

import joblib
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from src.db.database import engine
    from src.model.predict import predict_wp_dictionary
except ImportError:  # pragma: no cover - fallback for direct script execution
    from db.database import engine
    from model.predict import predict_wp_dictionary

app = FastAPI()

model = joblib.load(SRC_ROOT / "model" / "model.pkl")

class GameState(BaseModel):
    
    # total_home_score: int
    # total_away_score: int
    # qtr: int
    # game_seconds_remaining: int
    # yardline_100: int
    # goal_to_go: int
    # posteam_timeouts_remaining: int
    # defteam_timeouts_remaining: int
    
    game_seconds_remaining: int = Field(ge = 0, le = 3600)
    down: int = Field(ge = 0, le = 4)
    ydstogo: int = Field(ge = 1)
    home_yardline_100: int = Field(ge = 0, le = 100)
    
@app.post("/predict")
def predict(game_state : GameState):
    game_dict = game_state.model_dump()
        
    return predict_wp_dictionary(model, game_dict);
    
@app.get("/standings")
def get_standings():
    if engine is None:
        return []

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM standings")
        )

    return [dict(row) for row in result.mappings()]