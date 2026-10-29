
import pandas as pd

def predict_wp_dictionary(model, game_state):
    features = [
        "game_seconds_remaining",
        "down",
        "ydstogo",
        "home_yardline_100"
    ]

    X = pd.DataFrame([game_state])[features]

    probabilities = model.predict_proba(X)[0]

    away_wp = probabilities[0]
    home_wp = probabilities[1]

    return [float(home_wp), float(away_wp)]

def predict_wp_array(model, game_state):

    X = pd.DataFrame(
        [game_state],
        columns=[
        "game_seconds_remaining",
        "down",
        "ydstogo",
        "home_yardline_100",
        ]
    )

    probabilities = model.predict_proba(X)[0]

    # model classes are [0, 1] = [away, home]
    away_wp = probabilities[0]
    home_wp = probabilities[1]

    return [home_wp, away_wp]
