from fastapi import FastAPI
from pydantic import BaseModel, Field
from model.predict import predict_wp_dictionary
from model.next_play_model_testing import predict_wp_by_play
import joblib
from sqlalchemy import text
from db.database import engine


app = FastAPI()

old_model = joblib.load("src/model/old_model.pkl")
model = joblib.load("src/model/wp_play_model.joblib")

class oldGameState(BaseModel):
    
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
    
    
@app.post("/oldpredict")
def oldpredict(game_state : oldGameState):
    game_dict = game_state.model_dump()
        
    return predict_wp_dictionary(old_model, game_dict);

@app.post("/predict")
def predict(game_state : GameState):
    game_dict = game_state.model_dump()
        
    return predict_wp_by_play(model, game_dict);


@app.get("/standings")
def get_standings():
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM standings")
        )
        
    return [dict(row) for row in result.mappings()]

