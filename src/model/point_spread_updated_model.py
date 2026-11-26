# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.6
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
# # !pip install nflreadpy   # uncomment if the package hasn't already been installed

# %%
import joblib
import numpy as np
import pandas as pd
import nflreadpy as nfl
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# %%
import gc
import polars as pl
import nflreadpy as nfl
from nflreadpy.config import update_config
update_config(cache_mode="off")   # don't keep the raw download in RAM

start_season, end_season = 2006, 2026   # fewer seasons = less memory; widen if you have the RAM

# don't load all 370 columns, only the ones we actually need:
columns = [
    "season", "game_id", "play_type", "posteam", "home_team", "result",
    "game_seconds_remaining", "half_seconds_remaining", "down", "ydstogo",
    "yardline_100", "score_differential", "posteam_timeouts_remaining",
    "defteam_timeouts_remaining", "wp", "total_home_score", "total_away_score",
    "spread_line",
]
keep_plays = ["run", "pass", "punt", "field_goal", "qb_kneel", "qb_spike"]

# %%
# load one season at a time and trim it immediately so that the peak memory stays low instead of approaching max capacity early on in runtime
frames = []
for season in range(start_season, end_season + 1):
    frames.append(
        nfl.load_pbp(seasons=[season])
        .select(columns)
        .filter(pl.col("play_type").is_in(keep_plays))
    )

pbp_pandas = pl.concat(frames).to_pandas()
del frames
gc.collect()
#print(pbp_pandas.shape, round(pbp_pandas.memory_usage(deep=True).sum() / 1e6), "MB")

# %%
play_types = ["run", "pass", "punt", "field_goal"]

df = pbp_pandas[
    pbp_pandas["play_type"].isin(play_types)
    & pbp_pandas["posteam"].notna() #posteam means "team possessing the ball"
    & pbp_pandas["result"].notna()
    & (pbp_pandas["result"] != 0)
].copy()
#possessing team is the home team; boolean
df["posteam_is_home"] = (df["posteam"] == df["home_team"]).astype(int) 
#result column is margin of victory from perspective of home team. change the perspective to away team by flipping the sign if the possessing team is not the home team
pos_result = np.where(df["posteam_is_home"] == 1, df["result"], -df["result"]) 
#get whether the possessing team wins depending on whether the result, i.e. final score margin, is positive
df["posteam_win"] = (pos_result > 0).astype(int)

#nflverse's spread_line is positive when the HOME team is favored; flip the sign so that positive means the possessing team is favored
df["posteam_spread"] = np.where(df["posteam_is_home"] == 1, df["spread_line"], -df["spread_line"])

def add_spread_features(d):
    #needs game_seconds_remaining, score_differential and posteam_spread. gives the model the score and the spread as two separate time-scaled features,
    #so it can learn how much each is worth. the spread only counts for the share of the game still left to play; dividing by sqrt(time) scales both by how much the result can still swing
    frac_left = d["game_seconds_remaining"].clip(0, 3600) / 3600
    root_t = np.sqrt(d["game_seconds_remaining"] + 1)
    d["diff_per_sqrt_time"] = d["score_differential"] / root_t
    d["spread_per_sqrt_time"] = d["posteam_spread"] * frac_left / root_t
    return d

df = add_spread_features(df)
#converts play type column to fixed categories so that gradient boosting function can use it
df["play_type"] = pd.Categorical(df["play_type"].astype(str), categories=play_types)

features = [
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
features_play = features + ["play_type"]

required = ["posteam_win", "down", "ydstogo", "yardline_100", "score_differential", "game_seconds_remaining", "posteam_spread"]
model_df = df.dropna(subset=required)
train = model_df[model_df["season"] <= 2024]
test = model_df[model_df["season"] >= 2025]
y_train, y_test = train["posteam_win"], test["posteam_win"]
print(len(train), "train rows /", len(test), "test rows")
print(train["play_type"].value_counts())

# %% [markdown]
# comparing brier score loss on logistic vs gradient boosting vs adding play type to the latter

# %%
"""LR_NUM = [c for c in STATE if c != "down"]


def make_logistic():
    prep = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), LR_NUM),
        ("down_ohe", OneHotEncoder(handle_unknown="ignore"), ["down"]),
    ])
    return Pipeline([("prep", prep), ("clf", LogisticRegression(max_iter=1000))])
"""
#monotonic constraints: +1 = the prediction may only rise as the feature rises, -1 = it may only fall.
#a bigger lead, a bigger expected edge from the spread and more own timeouts can never lower win probability; more opponent timeouts can never raise it
monotonic_constraints = {
    "score_differential": 1,
    "diff_per_sqrt_time": 1,
    "spread_per_sqrt_time": 1,
    "posteam_timeouts_remaining": 1,
    "defteam_timeouts_remaining": -1,
}

def make_gb():
    return HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.08, max_leaf_nodes=31, min_samples_leaf=100,
        l2_regularization=1.0, early_stopping=False,
        monotonic_cst=monotonic_constraints,
        categorical_features="from_dtype",   # picks up the `play_type` category column
        random_state=42,
    )

"""lr_state = make_logistic().fit(train[features], y_train)"""
#baseline model: win probability from the game state alone, not conditional on the next play
gb_state = make_gb().fit(train[features], y_train)
gb_play = make_gb().fit(train[features_play], y_train)


# %%
def metrics(name, y, p):
    return {"model": name, "brier": brier_score_loss(y, p), "log_loss": log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)), "auc": roc_auc_score(y, p)}

#p_lr = lr_state.predict_proba(test[STATE])[:, 1]
p_gb_state = gb_state.predict_proba(test[features])[:, 1]
p_gb_play = gb_play.predict_proba(test[features_play])[:, 1]

pd.DataFrame([
    #metrics("logistic, state only", y_test, p_lr),
    metrics("boosting, state only", y_test, p_gb_state),
    metrics("boosting, state + play type", y_test, p_gb_play),
]).round(4)


# %% [markdown]
# interpretation: adding play type to the gradient boosting algorithm does not significantly skew the results. gradient boosting is a bit better than logistic which is good because one of its most important benefits is it can run on cpu even for a large dataset, which is what we need within the scope of this projext

# %% [markdown]
# ## win probaibility depending on next play
# keep game state fixed and swap the play for each iteration; return all results. plays are limited to sensible options. run/pass on downs 1-3; punt/field goal only available on 4th down.

# %%
def predict_wp_by_play(model, game_state):
    #game_state: dict with every key in features except the two derived ones, plus posteam_spread (+ = possessing team favored). return possession-team win probability for each allowed play.
    allowed = play_types if game_state["down"] == 4 else ["run", "pass"]
    rows = add_spread_features(pd.DataFrame([game_state] * len(allowed)))
    rows["play_type"] = pd.Categorical(allowed, categories=play_types)
    probs = model.predict_proba(rows[features_play])[:, 1]
    return pd.Series(probs, index=allowed, name="posteam_wp")

#test based on a few different game states
second_and_six = {
    "game_seconds_remaining": 600, "half_seconds_remaining": 600, "down": 2, "ydstogo": 6,
    "yardline_100": 45, "score_differential": 2,
    "posteam_timeouts_remaining": 3, "defteam_timeouts_remaining": 3, "posteam_is_home": 1,
    "posteam_spread": 3.0,
}
fourth_and_two = {
    "game_seconds_remaining": 600, "half_seconds_remaining": 600, "down": 4, "ydstogo": 2,
    "yardline_100": 35, "score_differential": -3,
    "posteam_timeouts_remaining": 2, "defteam_timeouts_remaining": 3, "posteam_is_home": 1,
    "posteam_spread": -1.0,
}
def predict_wp_baseline(model, game_state):
    #possession-team win probability from the game state alone, i.e. not conditional on the next play. model = the state-only model (gb_state)
    rows = add_spread_features(pd.DataFrame([game_state]))
    return float(model.predict_proba(rows[features])[0, 1])

print("baseline (any play):", round(predict_wp_baseline(gb_state, second_and_six), 4))
print(predict_wp_by_play(gb_play, second_and_six).round(4), "\n")
print("baseline (any play):", round(predict_wp_baseline(gb_state, fourth_and_two), 4))
print(predict_wp_by_play(gb_play, fourth_and_two).round(4))

# %%
joblib.dump(gb_play, "wp_play_model.joblib")

# %%
# # !pip install requests   # uncomment if it isn't installed
import json
import time
import requests
from IPython.display import clear_output, display

ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
HEADERS = {"User-Agent": "Mozilla/5.0 (class project)"}

def _get_scoreboard():
    r = requests.get(ESPN_SCOREBOARD, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()

def list_games():
    """show games that are on the current scoreboard. state is either 'pre', 'in' (live) or 'post'."""
    rows = []
    for ev in _get_scoreboard().get("events", []):
        t = ev.get("status", {}).get("type", {})
        rows.append({"event_id": ev.get("id"), "game": ev.get("shortName") or ev.get("name"),
                     "state": t.get("state"), "status": t.get("shortDetail")})
    return pd.DataFrame(rows)

def _find_event(data, event_id):
    ev = next((e for e in data.get("events", []) if str(e.get("id")) == str(event_id)), None)
    if ev is None:
        raise ValueError(f"event_id {event_id} is not on the current scoreboard. Run list_games().")
    return ev

def debug_raw_situation(event_id):
    """print the raw status and situation JSON so you can confirm the field names used below."""
    ev = _find_event(_get_scoreboard(), event_id)
    comp = ev["competitions"][0]
    print(json.dumps({"status": ev.get("status"), "situation": comp.get("situation")}, indent=2)[:4000])

def _clock_seconds(status):
    try:
        return float(status.get("clock"))
    except (TypeError, ValueError):
        pass
    try:
        m, s = str(status.get("displayClock", "0:00")).split(":")
        return int(m) * 60 + float(s)
    except Exception:
        return 0.0

def _time_remaining(period, clock):
    """returns (game_seconds_remaining, half_seconds_remaining). overtime uses the OT clock."""
    period = int(period)
    if period >= 5:
        return clock, clock
    game = (4 - period) * 900 + clock
    half = ((2 - period) if period <= 2 else (4 - period)) * 900 + clock
    return game, half

def _yardline_100(possession_text, pos_abbr):
    """possessionText like 'PHI 45' means the ball is on PHI's 45 yd line. convert to yards from the
    end zone the possession team is attacking. midfield is returned as is."""
    if not possession_text:
        return None
    parts = str(possession_text).split()
    try:
        n = int(parts[-1])
    except ValueError:
        return None
    if len(parts) == 1:
        return n
    return 100 - n if parts[0] == pos_abbr else n

ESPN_TO_NFLVERSE = {"WSH": "WAS", "LAR": "LA", "JAC": "JAX"}   # espn abbreviations that differ from nflverse's
_spread_cache = {}   # event_id -> (home spread, source). the pre-game line doesn't change during a game, so look it up once

def _spread_from_details(details, home_abbr, away_abbr):
    """espn odds text like 'BAL -4.5' means BAL is favored by 4.5. returns the spread with positive = HOME team favored, or None."""
    details = str(details or "").strip()
    if details.upper() in ("EVEN", "PK", "PICK", "PICK'EM", "PICKEM"):
        return 0.0
    parts = details.split()
    if len(parts) < 2 or parts[0] not in (home_abbr, away_abbr):
        return None
    try:
        favorite_margin = -float(parts[-1])      # 'BAL -4.5' -> BAL favored by 4.5
    except ValueError:
        return None
    return favorite_margin if parts[0] == home_abbr else -favorite_margin

def _spread_from_nflverse(home_abbr, away_abbr, season=None):
    """pre-game spread from nflverse's schedule file (positive = home favored): the same source and sign convention the model was trained on."""
    season = season or nfl.get_current_season()
    sched = nfl.load_schedules(seasons=[season]).to_pandas()
    home = ESPN_TO_NFLVERSE.get(home_abbr, home_abbr)
    away = ESPN_TO_NFLVERSE.get(away_abbr, away_abbr)
    games = sched[(sched["home_team"] == home) & (sched["away_team"] == away)]
    unplayed = games[games["result"].isna()]          #the game being played now has no final result yet
    games = unplayed if len(unplayed) else games
    if games.empty:
        return None
    value = games.iloc[0]["spread_line"]
    return None if pd.isna(value) else float(value)

def _spread_from_espn_core(event_id, home_abbr, away_abbr):
    """espn's odds endpoint for one game"""
    url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{event_id}/competitions/{event_id}/odds"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    for item in r.json().get("items", []):
        value = _spread_from_details(item.get("details"), home_abbr, away_abbr)
        if value is not None:
            return value
        spread, favorite = item.get("spread"), (item.get("homeTeamOdds") or {}).get("favorite")
        if spread is not None and favorite is not None:     #no readable text: use the number and the home-favorite flag
            return abs(float(spread)) if favorite else -abs(float(spread))
    return None

def _spread_sources(event_id, ev, comp, home_abbr, away_abbr):
    season = (ev.get("season") or {}).get("year")
    return [
        ("nflverse schedule", lambda: _spread_from_nflverse(home_abbr, away_abbr, season)),
        ("espn odds endpoint", lambda: _spread_from_espn_core(event_id, home_abbr, away_abbr)),
        ("espn scoreboard", lambda: _spread_from_details(((comp.get("odds") or [{}])[0]).get("details"), home_abbr, away_abbr)),
    ]

def _resolve_home_spread(event_id, ev, comp, home_abbr, away_abbr):
    """find the pre-game spread (positive = home team favored): nflverse first, then espn's odds endpoint, then the scoreboard feed.
    returns (spread or None, source name)."""
    key = str(event_id)
    if key in _spread_cache:
        return _spread_cache[key]
    for name, fetch in _spread_sources(event_id, ev, comp, home_abbr, away_abbr):
        try:
            value = fetch()
        except Exception:
            value = None
        if value is not None:
            _spread_cache[key] = (value, name)
            return value, name
    return None, None

def debug_spread_sources(event_id):
    """show what every spread source returns for this game, with the error if one fails, to see which ones work"""
    ev = _find_event(_get_scoreboard(), event_id)
    comp = ev["competitions"][0]
    sides = {c["homeAway"]: c for c in comp["competitors"]}
    home_abbr, away_abbr = sides["home"]["team"]["abbreviation"], sides["away"]["team"]["abbreviation"]
    print(f"{away_abbr} @ {home_abbr}, season {(ev.get('season') or {}).get('year')}. spreads are positive when the HOME team is favored")
    for name, fetch in _spread_sources(event_id, ev, comp, home_abbr, away_abbr):
        try:
            print(f"{name:20s}", fetch())
        except Exception as exc:
            print(f"{name:20s} FAILED: {type(exc).__name__}: {exc}")
    print("raw scoreboard odds:", comp.get("odds"))

def get_live_state(event_id, home_spread=None):
    """fetch one game and map it to the model's dictionary keys.
    home_spread (optional) overrides the spread from the feed: pre-game spread, positive = home team favored.
    returns {"state": dict or None, "meta": dict, "problems": [str]}."""
    ev = _find_event(_get_scoreboard(), event_id)
    comp = ev["competitions"][0]
    status = ev.get("status", comp.get("status", {}))
    sides = {c["homeAway"]: c for c in comp["competitors"]}
    home, away = sides["home"], sides["away"]
    sit = comp.get("situation") or {}
    problems = []

    meta = {
        "game": ev.get("shortName") or ev.get("name"),
        "status": status.get("type", {}).get("shortDetail"),
        "game_state": status.get("type", {}).get("state"),
        "home": home["team"].get("abbreviation"), "away": away["team"].get("abbreviation"),
        "home_score": int(home.get("score", 0)), "away_score": int(away.get("score", 0)),
        "possession_text": sit.get("possessionText"),
        "down_distance_text": sit.get("downDistanceText") or sit.get("shortDownDistanceText"),
    }

    if meta["game_state"] != "in":
        problems.append(f"game is not live (state = {meta['game_state']!r}).")
        return {"state": None, "meta": meta, "problems": problems}

    poss_id = str(sit.get("possession")) if sit.get("possession") is not None else None
    if poss_id == str(home["team"].get("id")):
        pos, dfn = home, away
    elif poss_id == str(away["team"].get("id")):
        pos, dfn = away, home
    else:
        problems.append("no team has possession in the feed right now (between plays, kickoff or timeout).")
        return {"state": None, "meta": meta, "problems": problems}

    down, dist = sit.get("down"), sit.get("distance")
    if down not in (1, 2, 3, 4) or dist is None:
        problems.append(f"no valid down/distance in the feed (down={down!r}, distance={dist!r}).")
        return {"state": None, "meta": meta, "problems": problems}

    yl = _yardline_100(sit.get("possessionText"), pos["team"].get("abbreviation"))
    if yl is None:
        problems.append("could not read the ball position from possessionText.")
        return {"state": None, "meta": meta, "problems": problems}

    clock = _clock_seconds(status)
    game_s, half_s = _time_remaining(status.get("period", 1), clock)

    to = {"home": sit.get("homeTimeouts"), "away": sit.get("awayTimeouts")}
    pos_side = "home" if pos is home else "away"
    def_side = "away" if pos is home else "home"
    for side in (pos_side, def_side):
        if to[side] is None:
            problems.append(f"{side} timeouts missing from the feed; assuming 3.")
            to[side] = 3

    spread_source = "you (home_spread=)"
    if home_spread is None:
        home_spread, spread_source = _resolve_home_spread(event_id, ev, comp, meta["home"], meta["away"])
    if home_spread is None:
        problems.append("could not find a pre-game spread from any source; using 0 (pick'em). pass home_spread= for better early-game accuracy, or run debug_spread_sources(event_id) to see why.")
        home_spread, spread_source = 0.0, "none, assumed 0"
    pos_spread = float(home_spread) if pos is home else -float(home_spread)
    meta["spread_source"] = spread_source

    state = {
        "game_seconds_remaining": game_s,
        "half_seconds_remaining": half_s,
        "down": int(down),
        "ydstogo": int(dist),
        "yardline_100": int(yl),
        "score_differential": int(pos.get("score", 0)) - int(dfn.get("score", 0)),
        "posteam_timeouts_remaining": int(to[pos_side]),
        "defteam_timeouts_remaining": int(to[def_side]),
        "posteam_is_home": 1 if pos is home else 0,
        "posteam_spread": float(pos_spread),
    }
    meta["posteam"] = pos["team"].get("abbreviation")
    return {"state": state, "meta": meta, "problems": problems}


# %%
def show_live(model, event_id, home_spread=None, baseline_model=None):
    """Fetch the live state, run the model, and print a readable summary.
    baseline_model = the state-only model (defaults to gb_state); its row is the win probability not conditional on the next play."""
    if baseline_model is None:
        baseline_model = gb_state
    snap = get_live_state(event_id, home_spread)
    m, state = snap["meta"], snap["state"]
    print(f"{m['game']}  |  {m['away']} {m['away_score']} - {m['home_score']} {m['home']}  |  {m['status']}")
    for p in snap["problems"]:
        print("note:", p)
    if state is None:
        print("No prediction right now.")
        return snap, None

    print(f"{m['posteam']} ball: {m['down_distance_text']} | ball on {m['possession_text']} "
          f"(yardline_100 = {state['yardline_100']}) | spread {state['posteam_spread']:+.1f} for {m['posteam']} ({m['spread_source']})")
    base = predict_wp_baseline(baseline_model, state)
    probs = pd.concat([pd.Series({"baseline (any play)": base}), predict_wp_by_play(model, state)])
    table = pd.DataFrame({
        f"{m['posteam']} win prob": probs.round(3),
        "vs baseline (pts)": ((probs - base) * 100).round(1),
        f"{m['home']} (home) win prob": (probs if state["posteam_is_home"] else 1 - probs).round(3),
    })
    table.index.name = "play called"
    display(table)
    #return snap, table

def watch_game(model, event_id, every=20, max_updates=90, home_spread=None):
    """Refresh the prediction every `every` seconds (minimum 15). Interrupt the kernel to stop."""
    every = max(every, 15)
    try:
        for _ in range(max_updates):
            clear_output(wait=True)
            try:
                show_live(model, event_id, home_spread)
            except Exception as exc:
                print("fetch failed, will retry:", exc)
            print(f"\n(updated {time.strftime('%H:%M:%S')}, refreshing every {every}s; stop the cell to quit)")
            time.sleep(every)
    except KeyboardInterrupt:
        print("stopped.")


# %% [markdown]
# ## how to use
# 1. call `list_games()` and copy an `event_id` for a game whose `state` is `in`.
# 2. during that game, run `debug_raw_situation(event_id)` once and check the keys (`down`, `distance`, `possession`, `possessionText`, `homeTimeouts`, `awayTimeouts`).
# 3. call `show_live(gb_play, event_id)` for a one-off prediction, or `watch_game(gb_play, event_id)` to auto-refresh.
# 4. the pre-game spread is looked up automatically (nflverse's schedule first, then espn's odds endpoint, then the scoreboard) and the source is printed with the situation. run `debug_spread_sources(event_id)` to see what each source returns. to override it, pass the pre-game spread yourself, e.g. `show_live(gb_play, event_id, home_spread=3.0)` (positive = home team favored).
# 5. the first row of the table, `baseline (any play)`, is the win probability from the game state alone, not conditional on the next play. the other rows are conditional on the play called, and `vs baseline (pts)` is the difference in percentage points.
#
#     sample usage below:

# %%
list_games()

# %%
EVENT_ID = 401873063 #replace this number after calling list_games
debug_raw_situation(EVENT_ID)
show_live(gb_play, EVENT_ID)
#watch_game(gb_play, EVENT_ID, every=20)

# %%
401873056

# %%
EVENT_ID = 401873062 #replace this number after calling list_games
#debug_raw_situation(EVENT_ID)
show_live(gb_play, EVENT_ID, home_spread=-6.5)
#watch_game(gb_play, EVENT_ID, every=20)

# %%
EVENT_ID = 401873065 #replace this number after calling list_games
#debug_raw_situation(EVENT_ID)
show_live(gb_play, EVENT_ID)
#watch_game(gb_play, EVENT_ID, every=20)

# %%
state = get_live_state(EVENT_ID, home_spread=4.5)["state"]
for spread in [-4.5, 0, 4.5]:      # posteam_spread: LAC's view, so -4.5 means LAC is a 4.5-point underdog
    print(spread, round(predict_wp_baseline(gb_state, {**state, "posteam_spread": spread}), 3))

# %%
