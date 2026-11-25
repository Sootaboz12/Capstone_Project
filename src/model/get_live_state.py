import numpy as np
import pandas as pd
import nflreadpy as nfl
import json
import requests
import time


ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
HEADERS = {"User-Agent": "Mozilla/5.0 (class project)"}

ESPN_TO_NFLVERSE = {"WSH": "WAS", "LAR": "LA", "JAC": "JAX"}   # espn abbreviations that differ from nflverse's
_spread_cache = {} 

# MAIN FUNCTION TO PARSE ESPN ENDPOINT FOR LIVE GAME STATE
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

    to = {"home": sit.get("homeTimeouts"),
          "away": sit.get("awayTimeouts")
    }
    
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

    pos_to = to[pos_side]
    def_to= to[def_side]
    
    assert pos_to is not None
    assert def_to is not None
    
    state = {
        "game_seconds_remaining": game_s,
        "half_seconds_remaining": half_s,
        "down": int(down),
        "ydstogo": int(dist),
        "yardline_100": int(yl),
        "score_differential": int(pos.get("score", 0)) - int(dfn.get("score", 0)),
        "posteam_timeouts_remaining": int(pos_to),
        "defteam_timeouts_remaining": int(def_to),
        "posteam_is_home": 1 if pos is home else 0,
        "posteam_spread": float(pos_spread),
    }
    meta["posteam"] = pos["team"].get("abbreviation")
    return {"state": state, "meta": meta, "problems": problems}


######################################
# HELPER FUNCTIONS FOR get_live_state#
######################################

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
