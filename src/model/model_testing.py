# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.6
#   kernelspec:
#     display_name: nfl-project (3.12.3)
#     language: python
#     name: python3
# ---

# %%
import sys
print(sys.executable)

# %%
# %load_ext autoreload
# %autoreload 2

from db.process import process_pbp, create_model_df

# %%
import pandas as pd

# %%
pbp = process_pbp()

model_df = create_model_df()

# %%
pbp_pandas = model_df.to_pandas()
# print(pbp_pandas)

# %%
#for i in pbp_pandas.columns:
    #print (i)

# %%
#pbp_pandas["score_diff"] = pbp_pandas["home_score"] - pbp_pandas["away_score"]

# %%
pbp_pandas["home_win"] = (pbp_pandas["result"] > 0).astype(int)

print(pbp_pandas["home_win"].value_counts())

# %%
features = [
    "game_seconds_remaining",
    "down",
    "ydstogo",
    "yardline_100",
    "home_win"
]
model_data = pbp_pandas[features].dropna()
features = [
    "game_seconds_remaining",
    "down",
    "ydstogo",
    "yardline_100",
]
X = model_data[features]
y = model_data["home_win"]

# %%
from sklearn.linear_model import LogisticRegression

model = LogisticRegression()

model.fit(X, y)

# %%
model.predict_proba(X)

# %%
print(
    pbp_pandas[
        ["game_id",
         "total_home_score",
         "total_away_score",
         "result",
         "home_win"]
    ].head(400).to_string()
)


# %%
def predict_wp_dictionary(model, game_state):

    features = [
        "game_seconds_remaining",
        "down",
        "ydstogo",
        "yardline_100"
    ]

    X = pd.DataFrame([game_state])[features]

    probabilities = model.predict_proba(X)[0]

    away_wp = probabilities[0]
    home_wp = probabilities[1]

    return [home_wp, away_wp]


# %%
gs1 = {
    "game_seconds_remaining": 600,
    "down": 2,
    "ydstogo": 6,
    "yardline_100": 45,
}


# %%
predict_wp_dictionary(model, gs1)


# %%
def predict_wp_array(model, game_state):

    X = pd.DataFrame(
        [game_state],
        columns=[
        "game_seconds_remaining",
        "down",
        "ydstogo",
        "yardline_100",
        ]
    )

    probabilities = model.predict_proba(X)[0]

    # model classes are [0, 1] = [away, home]
    away_wp = probabilities[0]
    home_wp = probabilities[1]

    return [home_wp, away_wp]


# %%
gs1 = [600, 2, 6, 45]

predict_wp_array(model, gs1)

# %%
train = pbp_pandas[pbp_pandas["season"] <= 2024]
test  = pbp_pandas[pbp_pandas["season"] >= 2025]

# %%
X_train = train[features].dropna()
y_train = train.loc[X_train.index, "home_win"]

X_test = test[features].dropna()
y_test = test.loc[X_test.index, "home_win"]

# %%
model2= LogisticRegression()

# %%
model.fit(X_train, y_train)

# %%
test_probs = model.predict_proba(X_test)

# %%
test_probs

# %%
from sklearn.metrics import brier_score_loss

brier = brier_score_loss(y_test, test_probs)

print("Brier score:", brier)
