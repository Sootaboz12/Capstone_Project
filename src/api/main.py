from fastapi import FastAPI
from pydantic import BaseModel, Field
from model.predict import predict_wp_dictionary
import joblib
from sqlalchemy import text
from db.database import engine

app = FastAPI()

model = joblib.load("src/model/model.pkl")

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
    
class GameState(BaseModel):

    game_seconds_remaining: int = Field(ge = 0, le = 3600)
    half_seconds_remaining: int = Field(ge=0, le=1800)
    down: int = Field(ge = 0, le = 4)
    ydstogo: int = Field(ge = 1)
    yardline_100: int = Field(ge = 0, le = 100)
    score_differential: int
    posteam_timeouts_remaining: int = Field(ge=0, le=3)
    defteam_timeouts_remaining: int = Field(ge=0, le=3)
    posteam_is_home: bool
    
# old prediction for first prototype
@app.post("/predict/old")
def oldpredict(game_state : oldGameState):
    game_dict = game_state.model_dump()
        
    return predict_wp_dictionary(old_model, game_dict);

# manual user input prediction on model in next_play_model
@app.post("/predict")
def predict(game_state : GameState):
    game_dict = game_state.model_dump()
        
    return predict_wp_by_play(model, game_dict).to_dict();

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
            "name": game["name"] 
        }
        for game in games
        if game["status"]["type"]["state"] == "in"
    ]
    
    return live_games

# get standings data, the format is the same of Google NFL standings widget
@app.get("/standings")
def get_standings():
    if engine is None:
        return []

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM standings")
        )

    return [dict(row) for row in result.mappings()]

