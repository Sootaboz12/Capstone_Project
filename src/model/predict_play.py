import numpy as np
import pandas as pd

PLAY_TYPES = ["run", "pass", "punt", "field_goal"]

FEATURES = [
    "game_seconds_remaining",
    "half_seconds_remaining",
    "down",
    "ydstogo",
    "yardline_100",
    "score_differential",
    "posteam_timeouts_remaining",
    "defteam_timeouts_remaining",
    "posteam_is_home",
    "diff_per_sqrt_time",
    "spread_per_sqrt_time",
]

FEATURES_PLAY = FEATURES + ["play_type"]


def add_spread_features(d):
    frac_left = d["game_seconds_remaining"].clip(0, 3600) / 3600
    root_t = np.sqrt(d["game_seconds_remaining"] + 1)

    d["diff_per_sqrt_time"] = d["score_differential"] / root_t
    d["spread_per_sqrt_time"] = d["posteam_spread"] * frac_left / root_t

    return d


def predict_wp_by_play(model, game_state):
    allowed = PLAY_TYPES if game_state["down"] == 4 else ["run", "pass"]

    rows = add_spread_features(
        pd.DataFrame([game_state] * len(allowed))
    )

    rows["play_type"] = pd.Categorical(
        allowed,
        categories=PLAY_TYPES
    )

    probs = model.predict_proba(rows[FEATURES_PLAY])[:, 1]

    return pd.Series(probs, index=allowed, name="posteam_wp")