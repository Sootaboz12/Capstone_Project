from fastapi import FastAPI
from pydantic import BaseModel, Field
from model.predict import predict_wp_dictionary
import joblib

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
    
@app.post("/predict")
def predict(game_state : GameState):
    game_dict = game_state.model_dump()
        
    return predict_wp_dictionary(model, game_dict);
    
