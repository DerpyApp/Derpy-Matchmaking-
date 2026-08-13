import streamlit as st
import pandas as pd
import requests
from pathlib import Path
from PIL import Image
from datetime import datetime, date, time as dtime

LOGO_PATH = Path(__file__).parent / "logo.png"
_logo_icon = Image.open(LOGO_PATH) if LOGO_PATH.exists() else "🏓"

from player_matchmaking import (
    SportType,
    FootballPosition,
    PadelPosition,
    Gender,
    TimeSlot,
    PlayerSportProfile,
    Player,
    MatchRequest,
    MatchmakingService,
)

st.set_page_config(page_title="Derpy Matchmaking Testing", page_icon=_logo_icon, layout="wide")

service = MatchmakingService()


def seed_players():
    return [
        Player(
            id=1, name="Ahmed", age=27, gender=Gender.MALE,
            preferred_latitude=30.0444, preferred_longitude=31.2357,  # Downtown Cairo
            sport_profiles=[
                PlayerSportProfile(sport=SportType.PADEL, skill_level=5, rating=4.2,
                                    number_of_matches=12, preferred_position=PadelPosition.NO_PREFERENCE),
            ],
        ),
        Player(
            id=2, name="Sara", age=24, gender=Gender.FEMALE,
            preferred_latitude=30.0626, preferred_longitude=31.2497,  # Nasr City
            sport_profiles=[
                PlayerSportProfile(sport=SportType.PADEL, skill_level=4, rating=3.8,
                                    number_of_matches=6, preferred_position=PadelPosition.LEFT),
            ],
        ),
        Player(
            id=3, name="Youssef", age=31, gender=Gender.MALE,
            preferred_latitude=30.0131, preferred_longitude=31.2089,  # Maadi
            sport_profiles=[
                PlayerSportProfile(sport=SportType.PADEL, skill_level=6, rating=4.6,
                                    number_of_matches=40, preferred_position=PadelPosition.RIGHT),
                PlayerSportProfile(sport=SportType.FOOTBALL, skill_level=5, rating=4.0,
                                    number_of_matches=20, preferred_position=FootballPosition.MIDFIELDER),
            ],
        ),
        Player(
            id=4, name="Mona", age=29, gender=Gender.FEMALE,
            preferred_latitude=30.0800, preferred_longitude=31.3300,  # Far from Downtown (~9km)
            sport_profiles=[
                PlayerSportProfile(sport=SportType.FOOTBALL, skill_level=3, rating=3.2,
                                    number_of_matches=3, preferred_position=FootballPosition.GOALKEEPER),
            ],
        ),
        Player(
            id=5, name="Karim", age=35, gender=Gender.MALE,
            preferred_latitude=30.1000, preferred_longitude=31.3500,
            preferred_times=[TimeSlot(day=0, start_time=dtime(17, 0), end_time=dtime(22, 0))],
            sport_profiles=[
                PlayerSportProfile(sport=SportType.PADEL, skill_level=2, rating=2.5,
                                    number_of_matches=1, preferred_position=PadelPosition.LEFT),
            ],
        ),
        Player(
            id=6, name="Nour", age=22, gender=Gender.FEMALE,
            preferred_latitude=None, preferred_longitude=None,  # no location
            sport_profiles=[
                PlayerSportProfile(sport=SportType.PADEL, skill_level=4, rating=3.9,
                                    number_of_matches=8, preferred_position=PadelPosition.NO_PREFERENCE),
            ],
        ),
        Player(
            id=7, name="Omar", age=26, gender=Gender.MALE,
            preferred_latitude=30.0500, preferred_longitude=31.2400,
            sport_profiles=[
                PlayerSportProfile(sport=SportType.FOOTBALL, skill_level=6, rating=4.5,
                                    number_of_matches=50, preferred_position=FootballPosition.FORWARD),
            ],
        ),
    ]


if "players" not in st.session_state:
    st.session_state.players = seed_players()
if "next_id" not in st.session_state:
    st.session_state.next_id = max(p.id for p in st.session_state.players) + 1

POSITIONS_BY_SPORT = {
    SportType.PADEL: list(PadelPosition),
    SportType.FOOTBALL: list(FootballPosition),
}



@st.cache_data(show_spinner=False)
def geocode_place(query: str):
    query = (query or "").strip()
    if not query:
        return None
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query,
                "format": "json",
                "limit": 1,
                "countrycodes": "eg", 
            },
            headers={"User-Agent": "DerpyMatchmakingTester/1.0"},
            timeout=8,
        )
        resp.raise_for_status()
        results = resp.json()
        if not results:
            return None
        return float(results[0]["lat"]), float(results[0]["lon"]), results[0].get("display_name", query)
    except Exception:
        return None


st.sidebar.header("➕ Add a new player")

st.sidebar.markdown("**🔎 Find location by name**")
st.sidebar.text_input(
    "Type an area/city (e.g. 'مدينة نصر، القاهرة' or 'New Cairo')",
    key="new_player_place_query",
)


def _locate_new_player():
    result = geocode_place(st.session_state.get("new_player_place_query", ""))
    if result:
        lat_val, lon_val, display_name = result
        st.session_state["new_player_lat"] = lat_val
        st.session_state["new_player_lon"] = lon_val
        st.session_state["new_player_geocode_msg"] = f"✅ {display_name}"
    else:
        st.session_state["new_player_geocode_msg"] = "⚠️ Place not found — enter coordinates manually below."


st.sidebar.button("📍 Locate", on_click=_locate_new_player, key="locate_new_player_btn")
if st.session_state.get("new_player_geocode_msg"):
    st.sidebar.caption(st.session_state["new_player_geocode_msg"])

with st.sidebar.form("add_player_form", clear_on_submit=True):
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0, max_value=100, value=25)
    gender = st.selectbox("Gender", [g.value for g in Gender])

    st.markdown("**Location**")
    lat = st.number_input(
        "Latitude", value=st.session_state.get("new_player_lat", 30.0444),
        format="%.4f", key="new_player_lat",
    )
    lon = st.number_input(
        "Longitude", value=st.session_state.get("new_player_lon", 31.2357),
        format="%.4f", key="new_player_lon",
    )
    has_location = st.checkbox("Has a preferred location", value=True)

    st.markdown("**Sport profile**")
    sport = st.selectbox("Sport", [s.value for s in SportType])
    skill_level = st.slider("Skill level (1-7)", 1.0, 7.0, 4.0, 0.5)
    rating = st.slider("Rating (1-5)", 1.0, 5.0, 3.0, 0.1)
    matches_played = st.number_input("Number of matches played", min_value=0, value=0)

    sport_enum = SportType(sport)
    position_choices = [p.value for p in POSITIONS_BY_SPORT[sport_enum]]
    position = st.selectbox("Preferred position", position_choices)

    st.markdown("**Preferred time (optional)**")
    has_time_pref = st.checkbox("Has a preferred time slot", value=False)
    day_choice = st.selectbox(
        "Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    )
    start_t = st.time_input("Start time", value=dtime(17, 0))
    end_t = st.time_input("End time", value=dtime(22, 0))

    submitted = st.form_submit_button("Add player")

    if submitted:
        if not name.strip():
            st.sidebar.error("Please enter a name.")
        else:
            if sport_enum == SportType.PADEL:
                pos_enum = PadelPosition(position)
            else:
                pos_enum = FootballPosition(position)

            preferred_times = []
            if has_time_pref:
                day_index = ["Monday", "Tuesday", "Wednesday", "Thursday",
                             "Friday", "Saturday", "Sunday"].index(day_choice)
                preferred_times.append(TimeSlot(day=day_index, start_time=start_t, end_time=end_t))

            new_player = Player(
                id=st.session_state.next_id,
                name=name.strip(),
                age=int(age),
                gender=Gender(gender),
                preferred_latitude=lat if has_location else None,
                preferred_longitude=lon if has_location else None,
                preferred_times=preferred_times,
                sport_profiles=[
                    PlayerSportProfile(
                        sport=sport_enum,
                        skill_level=skill_level,
                        rating=rating,
                        number_of_matches=int(matches_played),
                        preferred_position=pos_enum,
                    )
                ],
            )
            st.session_state.players.append(new_player)
            st.session_state.next_id += 1
            st.sidebar.success(f"Added {new_player.name}!")

st.sidebar.divider()
if st.sidebar.button("🗑️ Reset to sample players"):
    st.session_state.players = seed_players()
    st.session_state.next_id = max(p.id for p in st.session_state.players) + 1
    st.rerun()


header_logo, header_title = st.columns([1, 8], vertical_alignment="center")
with header_logo:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=90)
with header_title:
    st.title("Derpy Matchmaking Testing")
st.caption("Test the compatibility scoring model against a pool of players.")

tab_players, tab_match = st.tabs(["👥 Player pool", "🎯 Build a match request"])

# ---------------- Player pool tab ----------------
with tab_players:
    st.subheader(f"Player pool ({len(st.session_state.players)})")

    rows = []
    for p in st.session_state.players:
        for prof in p.sport_profiles:
            rows.append({
                "ID": p.id,
                "Name": p.name,
                "Age": p.age,
                "Gender": p.gender.value if p.gender else "-",
                "Location": f"{p.preferred_latitude:.3f}, {p.preferred_longitude:.3f}"
                            if p.preferred_latitude is not None else "— none —",
                "Sport": prof.sport.value,
                "Position": prof.preferred_position.value if prof.preferred_position else "-",
                "Skill": prof.skill_level,
                "Rating": prof.rating,
                "Matches played": prof.number_of_matches,
                "Time prefs": len(p.preferred_times),
            })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    remove_id = st.selectbox(
        "Remove a player",
        options=[None] + [p.id for p in st.session_state.players],
        format_func=lambda x: "—" if x is None else next(
            p.name for p in st.session_state.players if p.id == x
        ),
    )
    if remove_id is not None and st.button("Remove selected player"):
        st.session_state.players = [p for p in st.session_state.players if p.id != remove_id]
        st.rerun()

# ---------------- Match request tab ----------------
with tab_match:
    st.subheader("Define the match")

    st.markdown("**📍 Match location**")
    st.caption(
        f"📏 Location is a **soft factor**, not a hard cutoff: score falls off linearly to 0 at "
        f"{service.MAX_DISTANCE_KM:.0f} km, then keeps fading out to 0 at {service.SOFT_RANGE_KM:.0f} km. "
        "A missing or far-away location lowers a candidate's score but never removes them from the results."
    )

    place_col, btn_col = st.columns([4, 1])
    with place_col:
        st.text_input(
            "Search a place (e.g. 'مدينة نصر، القاهرة' or 'New Cairo')",
            key="match_place_query",
        )
    with btn_col:
        st.write("")

        def _locate_match():
            result = geocode_place(st.session_state.get("match_place_query", ""))
            if result:
                lat_val, lon_val, display_name = result
                st.session_state["req_lat"] = lat_val
                st.session_state["req_lon"] = lon_val
                st.session_state["match_geocode_msg"] = f"✅ {display_name}"
            else:
                st.session_state["match_geocode_msg"] = "⚠️ Place not found — enter coordinates manually below."

        st.button("Locate", on_click=_locate_match, key="locate_match_btn")

    if st.session_state.get("match_geocode_msg"):
        st.caption(st.session_state["match_geocode_msg"])

    col1, col2 = st.columns(2)
    with col1:
        req_sport = st.selectbox("Sport", [s.value for s in SportType], key="req_sport")
        req_sport_enum = SportType(req_sport)
        required_players = st.number_input(
            "Required players", min_value=1, value=4 if req_sport_enum == SportType.PADEL else 10
        )
        req_lat = st.number_input(
            "Match latitude", value=st.session_state.get("req_lat", 30.0444),
            format="%.4f", key="req_lat",
        )

    with col2:
        req_lon = st.number_input(
            "Match longitude", value=st.session_state.get("req_lon", 31.2357),
            format="%.4f", key="req_lon",
        )
        req_date = st.date_input("Match date", value=date(2026, 8, 10))
        req_time = st.time_input("Match time", value=dtime(18, 0))

    req_position_choices = [p.value for p in POSITIONS_BY_SPORT[req_sport_enum]]
    required_positions_raw = st.multiselect(
        "Required positions (leave empty = no position constraint)", req_position_choices
    )
    if req_sport_enum == SportType.PADEL:
        required_positions = [PadelPosition(p) for p in required_positions_raw]
    else:
        required_positions = [FootballPosition(p) for p in required_positions_raw]

    gender_filter = st.selectbox("Required gender", ["No constraint"] + [g.value for g in Gender])
    required_gender = None if gender_filter == "No constraint" else Gender(gender_filter)

    st.divider()
    st.markdown("### 👯 Already-confirmed players (optional)")
    st.caption(
        "If a group of friends is booking together, pick them here. They're locked into the "
        "match automatically — the matchmaking engine will only search for the remaining spots."
    )
    friend_names = st.multiselect(
        "Friend group already confirmed for this match",
        options=[p.id for p in st.session_state.players],
        format_func=lambda pid: next(p.name for p in st.session_state.players if p.id == pid),
    )
    confirmed_ids = set(friend_names)

    if st.button("🔍 Find matches", type="primary"):
        match_datetime = datetime.combine(req_date, req_time)

        confirmed_players = [p for p in st.session_state.players if p.id in confirmed_ids]
        candidate_pool = [p for p in st.session_state.players if p.id not in confirmed_ids]
        remaining_slots = int(required_players) - len(confirmed_players)

        remaining_positions = list(required_positions)
        for fp in confirmed_players:
            fprofile = fp.get_profile(req_sport_enum)
            if fprofile and fprofile.preferred_position in remaining_positions:
                remaining_positions.remove(fprofile.preferred_position)

        # -------- Confirmed squad summary --------
        if confirmed_players:
            st.subheader(f"👯 Confirmed friend group ({len(confirmed_players)})")
            confirmed_rows = []
            for p in confirmed_players:
                prof = p.get_profile(req_sport_enum)
                confirmed_rows.append({
                    "Name": p.name,
                    "Has profile for sport?": "Yes" if prof else "⚠️ No",
                    "Position": prof.preferred_position.value if prof and prof.preferred_position else "-",
                    "Skill": prof.skill_level if prof else "-",
                    "Gender": p.gender.value if p.gender else "-",
                })
            st.dataframe(pd.DataFrame(confirmed_rows), use_container_width=True, hide_index=True)

            missing_profile = [p.name for p in confirmed_players if p.get_profile(req_sport_enum) is None]
            if missing_profile:
                st.warning(
                    f"These confirmed players don't have a **{req_sport_enum.value}** profile, "
                    f"so they can't actually be validated for this sport: {', '.join(missing_profile)}"
                )

        if remaining_slots <= 0:
            st.success(
                f"The friend group already fills all {required_players} required spot(s) — "
                "no extra matchmaking needed."
            )
        else:
            st.info(f"Need **{remaining_slots}** more player(s) to complete the match.")

            request = MatchRequest(
                sport=req_sport_enum,
                required_players=remaining_slots,
                latitude=req_lat,
                longitude=req_lon,
                match_datetime=match_datetime,
                required_positions=remaining_positions,
                required_gender=required_gender,
            )

            ranked = service.rank_candidates(candidate_pool, request)

            st.subheader(f"Results ({len(ranked)} eligible candidate(s) to fill {remaining_slots} spot(s))")
            if not ranked:
                st.warning("No eligible candidates found to fill the remaining spots.")
            else:
                result_rows = []
                for player, score in ranked:
                    profile = player.get_profile(req_sport_enum)


                    location_score = service._score_location(player, request)
                    if player.preferred_latitude is None or player.preferred_longitude is None:
                        distance_display = "no location"
                    else:
                        distance_km = service._haversine_distance_km(
                            player.preferred_latitude, player.preferred_longitude,
                            request.latitude, request.longitude,
                        )
                        distance_display = f"{distance_km:.1f} km"

                    result_rows.append({
                        "Rank": None,
                        "Name": player.name,
                        "Score": round(score, 3),
                        "Distance": distance_display,
                        "Location score": round(location_score, 3),
                        "Skill": profile.skill_level,
                        "Rating": profile.rating,
                        "Matches played": profile.number_of_matches,
                        "Position": profile.preferred_position.value if profile.preferred_position else "-",
                        "Gender": player.gender.value if player.gender else "-",
                    })
                df = pd.DataFrame(result_rows)
                df["Rank"] = range(1, len(df) + 1)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.bar_chart(df.set_index("Name")["Score"])

                recommended = ranked[:remaining_slots]
                st.subheader(f"✅ Recommended full squad ({len(confirmed_players) + len(recommended)}/{required_players})")
                squad_rows = [{"Name": p.name, "Role": "Friend group (confirmed)"} for p in confirmed_players]
                squad_rows += [{"Name": p.name, "Role": f"Matched (score {s:.2f})"} for p, s in recommended]
                st.dataframe(pd.DataFrame(squad_rows), use_container_width=True, hide_index=True)

                if len(recommended) < remaining_slots:
                    st.warning(
                        f"Only found {len(recommended)} of the {remaining_slots} additional "
                        "player(s) needed — the pool doesn't have enough eligible candidates."
                    )

            all_ids = {p.id for p in candidate_pool}
            eligible_ids = {p.id for p, _ in ranked}
            excluded = [p for p in candidate_pool if p.id in (all_ids - eligible_ids)]
            with st.expander(f"Excluded / not eligible from the remaining pool ({len(excluded)})"):
                if excluded:
                    st.write(
                        "These players failed the hard eligibility gate: missing sport profile, "
                        "position mismatch, or gender mismatch. Note that location is no longer a "
                        "hard exclusion — a missing or far-away location now just lowers a player's "
                        "score (see the 'Location score' column above) instead of removing them from "
                        "the results. Confirmed friends are never excluded, since they're already "
                        "locked in."
                    )
                    st.dataframe(
                        pd.DataFrame([{"Name": p.name, "ID": p.id} for p in excluded]),
                        use_container_width=True, hide_index=True,
                    )
                else:
                    st.write("None — everyone remaining in the pool passed the eligibility gate.")
