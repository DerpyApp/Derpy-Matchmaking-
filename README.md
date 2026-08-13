# Derpy Matchmaking

AI-powered matchmaking engine for Derpy's sports-booking platform (padel & football), plus a Streamlit app for testing and tuning it interactively.

## What's in this repo

| File | Purpose |
|---|---|
| `player_matchmaking.py` | Core data model + `MatchmakingService` — the matchmaking/ranking algorithm |
| `app.py` | Streamlit UI for adding players, defining a match request, and inspecting ranked results |
| `requirements.txt` | Python dependencies |

## How matchmaking works

Given a `MatchRequest` (sport, location, datetime, required positions, optional required gender) and a pool of candidate `Player`s, `MatchmakingService.calculate_compatibility_score()` scores each candidate from `0.0` to `1.0` in two stages:

### 1. Eligibility gate (hard constraints)

A candidate is dropped entirely (score `0.0`) if any of these fail:

- **Sport** — must have a `PlayerSportProfile` for the requested sport.
- **Position** — must match one of the request's `required_positions`. Padel players registered as `NO_PREFERENCE` are treated as a wildcard and accepted for any position; football requires an exact match.
- **Gender** — only enforced if the request sets `required_gender`; otherwise ignored.

### 2. Weighted scoring (soft factors)

Candidates that pass the gate are scored on a weighted blend of:

| Factor | Weight | Notes |
|---|---|---|
| Skill | 0.35 | How close the player's skill level is to a baseline average |
| Location | 0.25 | **Soft factor** — see below |
| Rating | 0.20 | Player's rating out of 5 |
| Time availability | 0.10 | Whether the match time falls in the player's preferred slots (soft filter) |
| Experience | 0.10 | Scaled by number of matches played, capped at 20 |

**Location scoring is soft, not a hard cutoff:**
- No saved location → `0.0` on this factor only (the candidate still appears in results).
- Distance ≤ `MAX_DISTANCE_KM` (30 km) → linear falloff from `1.0` to `0.0`.
- Distance beyond that → keeps fading out linearly to `0.0` at `SOFT_RANGE_KM` (100 km), instead of dropping to zero abruptly.

This means a candidate is only ever excluded for sport/position/gender mismatches — distance and missing location just lower their rank.

`rank_candidates()` scores a full candidate list and returns them sorted best-first, with anyone who failed the eligibility gate removed.

## Running the testing app

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app lets you:
- Seed/add test players (with an optional "find location by name" geocoding search)
- Define a match request (sport, location, positions, required gender, datetime)
- See ranked results with a full score breakdown (skill, location, rating, time, experience) and excluded candidates with the reason

## Notes

- Geocoding ("Find location by name") uses the free OpenStreetMap Nominatim API, biased to Egypt (`countrycodes=eg`) to avoid ambiguous Arabic place names resolving to the wrong country.
- `logo.png` is optional — if present in the repo root next to `app.py`, it's used as the page icon; otherwise a default emoji is shown.
