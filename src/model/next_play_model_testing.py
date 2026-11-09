"""NFL next-play win-probability model, converted from the supplied notebook.

Importing this module does NOT download play-by-play data or train a model.

Examples (run from the Capstone project root):
    uv run python src/model/next_play_model.py train
    uv run python src/model/next_play_model.py games
    uv run python src/model/next_play_model.py show 401873022
    uv run python src/model/next_play_model.py watch 401873022 --every 20

The ESPN scoreboard endpoint used here is undocumented; its schema and availability
may change. Check the provider's terms before deploying an integration.
"""

import argparse
import gc
import json
import time
from pathlib import Path

import joblib
import nflreadpy as nfl
import numpy as np
import pandas as pd
import polars as pl
import requests
from sklearn.ensemble import HistGradientBoostingClassifier


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
]
FEATURES_PLAY = FEATURES + ["play_type"]

PBP_COLUMNS = [
    "season", "game_id", "play_type", "posteam", "home_team", "result",
    "game_seconds_remaining", "half_seconds_remaining", "down", "ydstogo",
    "yardline_100", "score_differential", "posteam_timeouts_remaining",
    "defteam_timeouts_remaining", "wp", "total_home_score", "total_away_score",
]
ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
HEADERS = {"User-Agent": "Mozilla/5.0 (class project)"}
DEFAULT_MODEL_PATH = Path(__file__).with_name("wp_play_model.joblib")


def load_model_data(start_season=2006, end_season=2026):
    """Load the selected PBP columns one season at a time to reduce peak memory."""
    from nflreadpy.config import update_config

    update_config(cache_mode="off")
    frames = []
    for season in range(start_season, end_season + 1):
        frames.append(
            nfl.load_pbp(seasons=[season])
            .select(PBP_COLUMNS)
            .filter(pl.col("play_type").is_in(PLAY_TYPES))
        )

    pbp_pandas = pl.concat(frames).to_pandas()
    del frames
    gc.collect()

    df = pbp_pandas[
        pbp_pandas["play_type"].isin(PLAY_TYPES)
        & pbp_pandas["posteam"].notna()
        & pbp_pandas["result"].notna()
        & (pbp_pandas["result"] != 0)
    ].copy()
    del pbp_pandas

    df["posteam_is_home"] = (df["posteam"] == df["home_team"]).astype(int)
    pos_result = np.where(df["posteam_is_home"] == 1, df["result"], -df["result"])
    df["posteam_win"] = (pos_result > 0).astype(int)
    df["play_type"] = pd.Categorical(df["play_type"].astype(str), categories=PLAY_TYPES)

    required = [
        "posteam_win", "down", "ydstogo", "yardline_100",
        "score_differential", "game_seconds_remaining",
    ]
    return df.dropna(subset=required)


def make_gb():
    """Same gradient-boosting model configuration used in the notebook."""
    return HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.08,
        max_leaf_nodes=31,
        min_samples_leaf=100,
        l2_regularization=1.0,
        early_stopping=False,
        categorical_features="from_dtype",
        random_state=42,
    )


def train_and_save_model(start_season=2006, end_season=2026, model_path=DEFAULT_MODEL_PATH):
    """Train on seasons through 2024, evaluate against seasons 2025 onward."""
    model_df = load_model_data(start_season, end_season)
    train = model_df[model_df["season"] <= 2024]
    test = model_df[model_df["season"] >= 2025]
    if train.empty:
        raise ValueError("No training rows available. Include seasons through 2024.")

    print(f"{len(train)} train rows / {len(test)} test rows")
    print(train["play_type"].value_counts())
    model = make_gb().fit(train[FEATURES_PLAY], train["posteam_win"])

    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    print(f"Saved model to {model_path}")
    return model


def predict_wp_by_play(model, game_state):
    """Return possession-team win probabilities for the allowed next play types."""
    allowed = PLAY_TYPES if game_state["down"] == 4 else ["run", "pass"]
    rows = pd.DataFrame([game_state] * len(allowed))
    rows["play_type"] = pd.Categorical(allowed, categories=PLAY_TYPES)
    probs = model.predict_proba(rows[FEATURES_PLAY])[:, 1]
    return pd.Series(probs, index=allowed, name="posteam_wp")


def _get_scoreboard():
    r = requests.get(ESPN_SCOREBOARD, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()


def list_games():
    """List games on ESPN's current scoreboard: pre, in (live), or post."""
    rows = []
    for ev in _get_scoreboard().get("events", []):
        t = ev.get("status", {}).get("type", {})
        rows.append({
            "event_id": ev.get("id"),
            "game": ev.get("shortName") or ev.get("name"),
            "state": t.get("state"),
            "status": t.get("shortDetail"),
        })
    return pd.DataFrame(rows)


def _find_event(data, event_id):
    ev = next(
        (e for e in data.get("events", []) if str(e.get("id")) == str(event_id)),
        None,
    )
    if ev is None:
        raise ValueError(f"event_id {event_id} is not on the current scoreboard. Run list_games().")
    return ev


def debug_raw_situation(event_id):
    """Print the raw ESPN status and situation for checking field names."""
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
    """Return (game_seconds_remaining, half_seconds_remaining). OT uses its own clock."""
    period = int(period)
    if period >= 5:
        return clock, clock
    game = (4 - period) * 900 + clock
    half = ((2 - period) if period <= 2 else (4 - period)) * 900 + clock
    return game, half


def _yardline_100(possession_text, pos_abbr):
    """Convert field position to yards from the possession team's attacking end zone."""
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


def get_live_state(event_id):
    """Return {'state': dict | None, 'meta': dict, 'problems': list[str]}."""
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
        "home": home["team"].get("abbreviation"),
        "away": away["team"].get("abbreviation"),
        "home_score": int(home.get("score", 0)),
        "away_score": int(away.get("score", 0)),
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
    }
    meta["posteam"] = pos["team"].get("abbreviation")
    return {"state": state, "meta": meta, "problems": problems}


def show_live(model, event_id):
    """Fetch one live game state, make predictions, and print a readable table."""
    snap = get_live_state(event_id)
    m, state = snap["meta"], snap["state"]
    print(f"{m['game']}  |  {m['away']} {m['away_score']} - {m['home_score']} {m['home']}  |  {m['status']}")
    for p in snap["problems"]:
        print("note:", p)
    if state is None:
        print("No prediction right now.")
        return snap, None

    print(
        f"{m['posteam']} ball: {m['down_distance_text']} | ball on {m['possession_text']} "
        f"(yardline_100 = {state['yardline_100']})"
    )
    probs = predict_wp_by_play(model, state)
    table = pd.DataFrame({
        f"{m['posteam']} win prob": probs,
        f"{m['home']} (home) win prob": probs if state["posteam_is_home"] else 1 - probs,
    }).round(3)
    table.index.name = "play called"
    print(table.to_string())  # Terminal equivalent of IPython.display.display(table)
    return snap, table


def watch_game(model, event_id, every=20, max_updates=90):
    """Poll a live game. Stop with Ctrl+C."""
    every = max(every, 15)
    try:
        for _ in range(max_updates):
            print("\n" + "=" * 65)
            try:
                show_live(model, event_id)
            except Exception as exc:
                print("fetch failed, will retry:", exc)
            print(f"\n(updated {time.strftime('%H:%M:%S')}, refreshing every {every}s; Ctrl+C to quit)")
            time.sleep(every)
    except KeyboardInterrupt:
        print("stopped.")


def main():
    
    # uv run python src/model/next_play_model-testing.py {train,games,debug,show,watch} 
    
    parser = argparse.ArgumentParser(description="NFL next-play win-probability model")
    parser.add_argument("action", choices=["train", "games", "debug", "show", "watch"])
    parser.add_argument("event_id", nargs="?", help="ESPN event ID for debug/show/watch")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--start-season", type=int, default=2006)
    parser.add_argument("--end-season", type=int, default=2026)
    parser.add_argument("--every", type=int, default=20, help="Polling interval in seconds")
    parser.add_argument("--max-updates", type=int, default=90)
    args = parser.parse_args()

    if args.action == "train":
        train_and_save_model(args.start_season, args.end_season, args.model)
        return
    if args.action == "games":
        print(list_games().to_string(index=False))
        return
    if not args.event_id:
        parser.error("event_id is required for debug/show/watch")
    if args.action == "debug":
        debug_raw_situation(args.event_id)
        return
    model = joblib.load(args.model)
    if args.action == "show":
        show_live(model, args.event_id)
    elif args.action == "watch":
        watch_game(model, args.event_id, every=args.every, max_updates=args.max_updates)


if __name__ == "__main__":
    main()
