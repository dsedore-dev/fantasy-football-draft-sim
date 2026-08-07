import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json
import urllib.request
import urllib.parse
import os
import urllib.error
import re
import base64

st.set_page_config(page_title="2026 Fantasy Draft Pro", page_icon="🏈", layout="wide")
st.markdown(
    """
    <style>
    :root{
        color-scheme: dark;
    }
    div[data-testid="stAppViewContainer"]{
        background: radial-gradient(1400px 700px at 20% -10%, #1e293b 0%, #0b1220 45%, #070b16 100%);
    }
    section[data-testid="stSidebar"]{
        background:#0f172a;
        border-right:1px solid #334155;
    }
    section[data-testid="stSidebar"] *{
        color:#e2e8f0;
    }
    div[data-testid="stMetric"]{
        background:#0f172a;
        border:1px solid #334155;
        border-radius:10px;
        padding:8px 10px;
    }
    div[data-testid="stDataFrame"]{
        border:1px solid #334155;
        border-radius:10px;
        overflow:hidden;
    }
    /* Force ALL primary buttons (including PICK) to blue */
    button[kind="primary"],
    div[data-testid="stBaseButton-primary"] button,
    div[data-testid="stBaseButton-primary"] > button {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
        color: #ffffff !important;
    }
    button[kind="primary"]:hover,
    div[data-testid="stBaseButton-primary"] button:hover,
    div[data-testid="stBaseButton-primary"] > button:hover {
        background-color: #1d4ed8 !important;
        border-color: #1d4ed8 !important;
        color: #ffffff !important;
    }
    button[kind="primary"]:focus,
    div[data-testid="stBaseButton-primary"] button:focus {
        box-shadow: 0 0 0 1px #1d4ed8 !important;
        outline: none !important;
    }
    div[data-testid="stAppViewContainer"] > .main > div.block-container{
        border:1px solid #334155;
        border-radius:12px;
        padding:0.9rem 1rem 1.1rem 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DEFAULT_LEAGUE_ID = "411675078"
KNOWN_MANAGER_OVERRIDES_BY_TEAM_ID = {
    1: "Daniel Decker",
}
KNOWN_MANAGER_ALIASES = {
    "ddecker88": "Daniel Decker",
}
DEFAULT_ESPN_S2 = (
    "AECVCqpjbfC/G4YUIcGJU3H5bvhzmtsGdby0JRBeRX1V8uXWD1PiFGFP/1Qs1P82FYrdROlckD+J+oo+dF0PJVdjtPchO2OqbyeC2fpxssNxljGUALXsElhNcsbYQ3I2yyxhR9AX5eDIUMsy+cIwJr/+L8TT5iu23TM3kZdZNY5knaCe4vYu5GvK+MsyLLgjkuT6iuuatSdSnydxw8lbHyN7D+//xixnF4t81YYlEW+G006LS6El5uRfYipvFMizv7e8QERMdFRZB60m4UygEeKGijH/b6yiJpbRrtHgl9dz5lqJbH7seU12RyQ5lHhBbpQ="
)
DEFAULT_LEAGUE_TEAMS = [
    {"team_id": 4, "name": "Drumsticks not dumb picks", "abbrev": "RLK", "logo": "https://g.espncdn.com/lm-static/ffl/images/default_logos/4.svg", "draft_slot": 1},
    {"team_id": 9, "name": "Lower Aidenn Lair", "abbrev": "WIZ", "logo": "https://g.espncdn.com/lm-static/logo-packs/ffl/OldeTymeFootball-AndrewJanik/Warriors_03.svg", "draft_slot": 2},
    {"team_id": 6, "name": "The London Silly Nannies", "abbrev": "LSN", "logo": "https://g.espncdn.com/lm-static/ffl/images/default_logos/6.svg", "draft_slot": 3},
    {"team_id": 13, "name": "JZ", "abbrev": "JZ", "logo": "https://g.espncdn.com/lm-static/ffl/images/default_logos/6.svg", "draft_slot": 4},
    {"team_id": 12, "name": "THE JPP FIREWORK SHOW", "abbrev": "OOPs", "logo": "https://g.espncdn.com/lm-static/ffl/images/default_logos/19.svg", "draft_slot": 5},
    {"team_id": 7, "name": "Philly Philly", "abbrev": "Phil", "logo": "https://g.espncdn.com/lm-static/ffl/images/default_logos/11.svg", "draft_slot": 6},
    {"team_id": 5, "name": "Mandlebaums", "abbrev": "MAn", "logo": "https://g.espncdn.com/lm-static/logo-packs/ffl/TeamKinny-MartinLaksman/TeamKinny-20.svg", "draft_slot": 7},
    {"team_id": 1, "name": "Vandelay Industries", "abbrev": "Van", "logo": "https://g.espncdn.com/lm-static/ffl/images/default_logos/1.svg", "draft_slot": 8},
    {"team_id": 2, "name": "Taco Corp", "abbrev": "CRPO", "logo": "https://ih1.redbubble.net/image.5019836217.8099/st,small,507x507-pad,600x600,f8f8f8.u1.jpg", "draft_slot": 9},
    {"team_id": 10, "name": "The Shiddy Beatles", "abbrev": "TSB", "logo": "https://g.espncdn.com/lm-static/ffl/images/default_logos/8.svg", "draft_slot": 10},
    {"team_id": 8, "name": "New York Bagels", "abbrev": "Bagl", "logo": "https://g.espncdn.com/lm-static/logo-packs/ffl/MickeyAndDonald-Disney/Disney-02.svg", "draft_slot": 11},
    {"team_id": 3, "name": "Laizze-Lair", "abbrev": "TRAU", "logo": "https://g.espncdn.com/lm-static/logo-packs/ffl/8bitHeros-JoeyEllis/8bit_football-06.svg", "draft_slot": 12},
]
ESPN_DEFAULT_POS_ID_TO_POS = {
    1: "QB",
    2: "RB",
    3: "WR",
    4: "TE",
    5: "K",
    16: "DEF",
}
ESPN_LINEUP_SLOT_TO_POS = {
    0: "QB",
    2: "RB",
    4: "WR",
    6: "TE",
    16: "DEF",
    17: "K",
}

# Load all data
@st.cache_data
def load_data():
    df_players = pd.read_csv('data/complete_player_database.csv')
    df_availability = pd.read_csv('data/player_availability_16_rounds.csv')
    df_sleepers = pd.read_csv('data/2026_ppr_sleepers_undervalued.csv')
    df_traps = pd.read_csv('data/2026_ppr_trap_picks_overvalued.csv')
    df_strategies = pd.read_csv('data/all_strategies_with_generic.csv')  # Updated to use merged strategies
    df_full_strategies = pd.read_csv('data/all_strategies_16_rounds_full_roster.csv')
    df_recommended = pd.read_csv('data/recommended_strategies_by_slot.csv')

    tier_candidates = [
        'new_tier_rankings.csv',
        'player_tier_rankings.csv',
        'data/new_tier_rankings.csv',
        'data/player_tier_rankings.csv',
    ]
    tier_frames = []
    for tier_path in tier_candidates:
        if not Path(tier_path).exists():
            continue
        tier_df = pd.read_csv(tier_path, usecols=['Player', 'Tier'])
        tier_df = tier_df.dropna(subset=['Player', 'Tier']).copy()
        tier_df['Player'] = tier_df['Player'].astype(str).str.strip()
        tier_df['Tier'] = pd.to_numeric(tier_df['Tier'], errors='coerce')
        tier_df = tier_df.dropna(subset=['Tier'])
        if not tier_df.empty:
            tier_frames.append(tier_df)

    if tier_frames:
        all_tiers = pd.concat(tier_frames, ignore_index=True)
        all_tiers = all_tiers.drop_duplicates(subset=['Player'], keep='first')
        if 'Tier' in df_players.columns:
            missing_tier = df_players['Tier'].isna()
            df_players = df_players.copy()
            df_players.loc[missing_tier, 'Tier'] = df_players.loc[missing_tier, 'Player'].map(
                all_tiers.set_index('Player')['Tier']
            )
        else:
            df_players = df_players.merge(all_tiers, on='Player', how='left')

    # Merge player headshots
    if Path('data/player_images.csv').exists():
        df_images = pd.read_csv('data/player_images.csv', usecols=['Player', 'Headshot_URL'])
        df_images = df_images.dropna(subset=['Player'])
        df_images['Player'] = df_images['Player'].astype(str).str.strip()
        df_players = df_players.merge(df_images, on='Player', how='left')

    return df_players, df_availability, df_sleepers, df_traps, df_strategies, df_full_strategies, df_recommended

df_players, df_availability, df_sleepers, df_traps, df_strategies, df_full_strategies, df_recommended_strategies = load_data()


def _get_local_secret(name):
    try:
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    return str(os.getenv(name, "")).strip()


# Initialize session state
if "draft_started" not in st.session_state:
    st.session_state.draft_started = False
if "draft_slot" not in st.session_state:
    st.session_state.draft_slot = None
if "drafted_players" not in st.session_state:
    st.session_state.drafted_players = []
if "current_round" not in st.session_state:
    st.session_state.current_round = 1
if "strategy" not in st.session_state:
    st.session_state.strategy = None
if "selected_player_info" not in st.session_state:
    st.session_state.selected_player_info = None
if "espn_s2" not in st.session_state:
    st.session_state.espn_s2 = _get_local_secret("ESPN_S2") or DEFAULT_ESPN_S2
if "espn_swid" not in st.session_state:
    st.session_state.espn_swid = _get_local_secret("SWID")
if "espn_league_id" not in st.session_state:
    st.session_state.espn_league_id = DEFAULT_LEAGUE_ID
if "espn_selected_team_id" not in st.session_state:
    st.session_state.espn_selected_team_id = None
if "espn_selected_team_name" not in st.session_state:
    st.session_state.espn_selected_team_name = None
if "espn_selected_owner_id" not in st.session_state:
    st.session_state.espn_selected_owner_id = None
if "espn_selected_owner_name" not in st.session_state:
    st.session_state.espn_selected_owner_name = None
if "espn_connected" not in st.session_state:
    st.session_state.espn_connected = False
if "espn_connect_status" not in st.session_state:
    st.session_state.espn_connect_status = ""
if "espn_teams_cache" not in st.session_state:
    st.session_state.espn_teams_cache = DEFAULT_LEAGUE_TEAMS.copy()
if "app_page" not in st.session_state:
    st.session_state.app_page = "Landing"
if "team_view_team_id" not in st.session_state:
    st.session_state.team_view_team_id = None


ROSTER_REQUIREMENTS = {
    "QB": 1,
    "RB": 2,
    "WR": 2,
    "TE": 1,
    "FLEX": 1,   # RB/WR/TE
    "DEF": 1,
    "K": 1,
    "BENCH": 6
}

ANIMAL_TEAMS = {
    "ARI",  # Cardinals
    "ATL",  # Falcons
    "BAL",  # Ravens
    "BUF",  # Bills (Buffalo)
    "CAR",  # Panthers
    "CHI",  # Bears
    "CIN",  # Bengals
    "DEN",  # Broncos
    "DET",  # Lions
    "IND",  # Colts
    "JAX",  # Jaguars
    "LAR",  # Rams
    "MIA",  # Dolphins
    "PHI",  # Eagles
    "SEA",  # Seahawks
}


def normalize_player_name(name):
    cleaned = str(name or "").lower().strip()
    for token in [" jr.", " jr", " sr.", " sr", " ii", " iii", " iv"]:
        cleaned = cleaned.replace(token, "")
    cleaned = "".join(ch for ch in cleaned if ch.isalnum() or ch.isspace())
    return " ".join(cleaned.split())


def normalize_team_abbr(team):
    team_abbr = str(team or "").upper().strip()
    if team_abbr == "JAC":
        return "JAX"
    if team_abbr == "WAS":
        return "WSH"
    return team_abbr


def normalize_owner_id(owner_id):
    val = str(owner_id or "").strip().lower()
    return val.strip("{}")


def resolve_member_name(member):
    first = str(member.get("firstName") or "").strip()
    last = str(member.get("lastName") or "").strip()
    if first or last:
        return " ".join([p for p in [first, last] if p]).strip()
    display = str(member.get("displayName") or "").strip()
    if display and not re.match(r"^espn[a-z0-9_-]*$", display, flags=re.IGNORECASE):
        return display
    return "Unknown manager"


def normalize_manager_name(name):
    n = str(name or "").strip()
    if not n:
        return "Unknown manager"
    if re.match(r"^espn[a-z0-9_-]*$", n, flags=re.IGNORECASE):
        return "Unknown manager"
    return n


def resolve_manager_label(raw_name, team_name="", team_id=None):
    alias_key = str(raw_name or "").strip().lower()
    if alias_key in KNOWN_MANAGER_ALIASES:
        return KNOWN_MANAGER_ALIASES[alias_key]
    if team_id in KNOWN_MANAGER_OVERRIDES_BY_TEAM_ID:
        return KNOWN_MANAGER_OVERRIDES_BY_TEAM_ID[team_id]
    manager = normalize_manager_name(raw_name)
    if manager != "Unknown manager":
        return manager
    team_name = str(team_name or "").strip()
    if team_name:
        return f"{team_name} manager"
    return "Manager unavailable"


def get_team_manager_display(team):
    team_name = str(team.get("name") or f"Team {team.get('team_id', '')}").strip()
    return resolve_manager_label(team.get("owner"), team_name, team.get("team_id"))


def _merge_manager_name(raw_name, owner_id, canonical_by_owner_id, team_name="", team_id=None):
    raw = resolve_manager_label(raw_name, team_name, team_id)
    owner_key = normalize_owner_id(owner_id)
    canonical = resolve_manager_label(canonical_by_owner_id.get(owner_key, ""), team_name, team_id)
    generic_values = {"Unknown manager", "Manager unavailable", f"{team_name} manager"}
    if raw in generic_values and canonical not in generic_values:
        return canonical
    return raw


def infer_draft_strategy_label(first_positions):
    positions = [str(p).upper().strip() for p in first_positions if str(p).strip() and str(p).strip() != "—"]
    if not positions:
        return "Unknown"
    counts = pd.Series(positions).value_counts().to_dict()
    first = positions[0]
    rb = int(counts.get("RB", 0))
    wr = int(counts.get("WR", 0))
    te = int(counts.get("TE", 0))
    qb = int(counts.get("QB", 0))
    if first == "QB":
        return "Early QB"
    if first == "TE":
        return "Early TE"
    if rb >= 3 and wr <= 1:
        return "RB Heavy"
    if wr >= 3 and rb <= 1:
        return "WR Heavy"
    if rb >= 2 and wr >= 2:
        return "Balanced RB/WR"
    if rb >= 2 and te >= 1:
        return "RB + TE Mix"
    if wr >= 2 and qb >= 1:
        return "WR + QB Mix"
    return "Mixed"


@st.cache_data(ttl=21600, show_spinner=False)
def resolve_team_logo_src(logo_url, espn_s2="", swid="", fallback_logo=""):
    url = str(logo_url or "").strip()
    fallback = str(fallback_logo or "").strip()
    if not url:
        return fallback
    if "mystique-api.fantasy.espn.com" not in url:
        return url
    try:
        cookie = _build_espn_cookie(espn_s2, swid) if str(espn_s2 or "").strip() else ""
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "image/*"}
        if cookie:
            headers["Cookie"] = cookie
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read()
            content_type = response.headers.get("Content-Type", "image/png").split(";")[0].strip() or "image/png"
        if not content_type.lower().startswith("image/") or not raw:
            return fallback or url
        encoded = base64.b64encode(raw).decode("ascii")
        return f"data:{content_type};base64,{encoded}"
    except Exception:
        return fallback or url


@st.cache_data(ttl=1800, show_spinner=False)
def load_espn_league_teams(league_id, season, espn_s2, swid=""):
    league_id = str(league_id).strip()
    season = int(season)
    espn_s2 = str(espn_s2 or "").strip()
    swid = str(swid or "").strip()
    if not league_id or not espn_s2:
        return []

    url = (
        f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/"
        f"leagues/{league_id}?view=mTeam&view=mDraftDetail"
    )
    cookie = f"espn_s2={espn_s2}"
    if swid:
        cookie += f"; SWID={swid}"
    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0", "Cookie": cookie}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        data = json.loads(response.read().decode())

    members = {
        normalize_owner_id(m.get("id")): resolve_member_name(m)
        for m in data.get("members", [])
    }

    slot_by_team = {}
    picks = data.get("draftDetail", {}).get("picks", [])
    round1 = [p for p in picks if p.get("roundId") == 1 and p.get("roundPickNumber") is not None]
    for p in sorted(round1, key=lambda x: x.get("roundPickNumber", 999)):
        slot_by_team[p.get("teamId")] = int(p.get("roundPickNumber"))

    teams = []
    for t in data.get("teams", []):
        owner_id = (t.get("owners") or [None])[0]
        owner_key = normalize_owner_id(owner_id)
        team_id = t.get("id")
        team_name = t.get("name") or t.get("abbrev") or f"Team {team_id}"
        teams.append(
            {
                "team_id": team_id,
                "name": team_name,
                "abbrev": t.get("abbrev", ""),
                "owner_id": owner_id,
                "owner": resolve_manager_label(members.get(owner_key, ""), team_name, team_id),
                "logo": t.get("logo", ""),
                "logo_resolved": resolve_team_logo_src(
                    t.get("logo", ""),
                    espn_s2,
                    swid,
                    f"https://g.espncdn.com/lm-static/ffl/images/default_logos/{(int(team_id or 1) % 20) or 1}.svg",
                ),
                "draft_slot": slot_by_team.get(team_id),
            }
        )
    teams.sort(key=lambda x: (x["draft_slot"] is None, x["draft_slot"] or 999, x["name"]))
    return teams


@st.cache_data(ttl=21600, show_spinner=False)
def load_sleeper_data():
    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}

    def fetch_json(url):
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode())

    players = fetch_json("https://api.sleeper.app/v1/players/nfl")
    projections_2026 = fetch_json(
        "https://api.sleeper.app/v1/projections/nfl/regular/2026?position[]=QB&position[]=RB&position[]=WR&position[]=TE&order_by=pts_ppr"
    )
    stats_2024 = fetch_json(
        "https://api.sleeper.app/v1/stats/nfl/regular/2024?position[]=QB&position[]=RB&position[]=WR&position[]=TE&order_by=pts_ppr"
    )
    return players, projections_2026, stats_2024


@st.cache_data(ttl=21600, show_spinner=False)
def load_sleeper_weekly_projections(player_id, season=2026):
    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    url = (
        f"https://api.sleeper.com/projections/nfl/player/{player_id}"
        f"?season_type=regular&season={int(season)}&grouping=week"
    )
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode())


def find_sleeper_player(players_map, player_name, team, position):
    target_name = normalize_player_name(player_name)
    target_team = normalize_team_abbr(team)
    target_pos = str(position or "").upper().strip()

    candidates = []
    for pid, p in players_map.items():
        full_name = p.get("full_name", "")
        if normalize_player_name(full_name) != target_name:
            continue
        candidates.append((pid, p))

    if not candidates:
        return None, None

    for pid, p in candidates:
        team_abbr = normalize_team_abbr(p.get("team") or p.get("team_abbr"))
        pos = str(p.get("position", "")).upper().strip()
        if team_abbr == target_team and pos == target_pos:
            return pid, p

    for pid, p in candidates:
        pos = str(p.get("position", "")).upper().strip()
        if pos == target_pos:
            return pid, p

    return candidates[0][0], candidates[0][1]


def get_pick_number(round_num, slot, teams=12):
    if round_num % 2 == 1:
        return (round_num - 1) * teams + slot
    return round_num * teams - slot + 1


def get_strategy_row(slot, strategy_name):
    match = df_full_strategies[
        (df_full_strategies["Slot"] == slot) &
        (df_full_strategies["Strategy_Name"] == strategy_name)
    ]
    if match.empty:
        return None
    return match.iloc[0]


def is_animal_team(team_abbr):
    return str(team_abbr).strip().upper() in ANIMAL_TEAMS


def get_planned_round_for_player(strategy_row, player_name):
    if strategy_row is None:
        return None
    name = str(player_name).strip()
    if not name:
        return None

    for round_num in range(1, 17):
        round_pick_col = f"Round{round_num}_Pick"
        if round_pick_col not in strategy_row.index or pd.isna(strategy_row[round_pick_col]):
            continue

        planned_pick = str(strategy_row[round_pick_col]).strip()
        if planned_pick == "No player available" or planned_pick == "":
            continue
        if planned_pick == name:
            return round_num

    return None


def get_strategy_fit_label(player_row, strategy_row, current_round):
    if strategy_row is None:
        return "—"

    strategy_name = str(strategy_row.get("Strategy_Name", "")).strip().lower()
    if "ryans-animal" in strategy_name:
        return "✅" if is_animal_team(player_row.get("Team", "")) else "❌"

    expected_pos = None
    round_pos_col = f"Round{current_round}_Pos"
    if round_pos_col in strategy_row.index and pd.notna(strategy_row[round_pos_col]):
        expected_pos = str(strategy_row[round_pos_col]).strip().upper()

    player_pos = str(player_row.get("Position", "")).strip().upper()
    player_name = str(player_row.get("Player", "")).strip()
    if not player_name and not player_pos:
        return "—"

    # Jets-Focus is a named-player strategy with a tolerated one-round slip.
    if strategy_name == "jets-focus":
        planned_round = get_planned_round_for_player(strategy_row, player_name)
        if planned_round is None:
            return "❌"
        return "✅" if (planned_round - 1) <= current_round <= (planned_round + 1) else "❌"

    # Standard strategies are position-driven (e.g., WR-Heavy should mark all WR as in-strategy).
    if expected_pos:
        if expected_pos in {"", "NO PLAYER AVAILABLE"}:
            return "—"
        if expected_pos == "FLEX":
            return "✅" if player_pos in {"RB", "WR", "TE"} else "❌"
        return "✅" if player_pos == expected_pos else "❌"

    # Fallback: if a strategy round only has a named pick and no position, match by name.
    planned_round = get_planned_round_for_player(strategy_row, player_name)
    if planned_round is None:
        return "—"
    return "✅" if planned_round == current_round else "❌"


def get_roster_status(drafted_players):
    counts = {"QB": 0, "RB": 0, "WR": 0, "TE": 0, "DEF": 0, "K": 0}
    for p in drafted_players:
        pos = p.get("pos")
        if pos in counts:
            counts[pos] += 1

    remaining_starters = {
        "QB": max(ROSTER_REQUIREMENTS["QB"] - counts["QB"], 0),
        "RB": max(ROSTER_REQUIREMENTS["RB"] - counts["RB"], 0),
        "WR": max(ROSTER_REQUIREMENTS["WR"] - counts["WR"], 0),
        "TE": max(ROSTER_REQUIREMENTS["TE"] - counts["TE"], 0),
        "DEF": max(ROSTER_REQUIREMENTS["DEF"] - counts["DEF"], 0),
        "K": max(ROSTER_REQUIREMENTS["K"] - counts["K"], 0),
    }

    extra_flex_pool = max(counts["RB"] - 2, 0) + max(counts["WR"] - 2, 0) + max(counts["TE"] - 1, 0)
    flex_filled = min(extra_flex_pool, ROSTER_REQUIREMENTS["FLEX"])
    remaining_flex = ROSTER_REQUIREMENTS["FLEX"] - flex_filled

    starters_filled = (
        min(counts["QB"], 1) + min(counts["RB"], 2) + min(counts["WR"], 2) +
        min(counts["TE"], 1) + min(counts["DEF"], 1) + min(counts["K"], 1)
    )
    bench_filled = max(len(drafted_players) - starters_filled - flex_filled, 0)
    remaining_bench = max(ROSTER_REQUIREMENTS["BENCH"] - bench_filled, 0)

    return remaining_starters, remaining_flex, remaining_bench


def get_suggested_player(available_players, strategy_row, round_num, remaining_starters, remaining_flex, remaining_bench):
    if available_players.empty:
        return None

    need_positions = []
    for pos in ["QB", "RB", "WR", "TE", "DEF", "K"]:
        if remaining_starters[pos] > 0:
            need_positions.append(pos)

    if remaining_flex > 0:
        need_positions.extend(["RB", "WR", "TE"])

    if remaining_bench > 0 and len(need_positions) == 0:
        need_positions.extend(["RB", "WR", "TE", "QB", "DEF", "K"])

    expected_pos = None
    if strategy_row is not None:
        round_pos_col = f"Round{round_num}_Pos"
        if round_pos_col in strategy_row.index and pd.notna(strategy_row[round_pos_col]):
            expected_pos = str(strategy_row[round_pos_col]).upper()

    candidates = available_players.copy()
    if need_positions:
        candidates = candidates[candidates["Position"].isin(need_positions)]
        if candidates.empty:
            candidates = available_players.copy()

    if strategy_row is not None:
        strategy_name = str(strategy_row.get("Strategy_Name", "")).strip()
        strategy_name_l = strategy_name.lower()
        if "ryans-animal" in strategy_name_l:
            animal_candidates = candidates[candidates["Team"].apply(is_animal_team)].copy()
            if not animal_candidates.empty:
                candidates = animal_candidates

        if strategy_name == "Jets-Focus":
            jets_candidates = candidates[candidates["Team"].fillna("").str.upper() == "NYJ"].copy()
            if not jets_candidates.empty:
                jets_candidates["Planned_Round"] = jets_candidates["Player"].apply(
                    lambda n: get_planned_round_for_player(strategy_row, n)
                )
                jets_candidates = jets_candidates[jets_candidates["Planned_Round"].notna()].copy()
                if not jets_candidates.empty:
                    jets_candidates["Round_Delta"] = (jets_candidates["Planned_Round"] - round_num).abs()
                    near_plan = jets_candidates[jets_candidates["Round_Delta"] <= 1].copy()
                    if not near_plan.empty:
                        return near_plan.sort_values(["Round_Delta", "ADP_Resolved"]).iloc[0]
                    return jets_candidates.sort_values(["Planned_Round", "ADP_Resolved"]).iloc[0]

    if expected_pos and expected_pos in candidates["Position"].unique():
        expected_pool = candidates[candidates["Position"] == expected_pos]
        if not expected_pool.empty:
            return expected_pool.sort_values("ADP_Resolved").iloc[0]

    return candidates.sort_values("ADP_Resolved").iloc[0]


def build_player_pool(players_df, drafted_names, allowed_positions=None):
    pool = players_df[~players_df['Player'].isin(drafted_names)].copy()
    pool = pool[pool['Team'].notna()].copy()
    pool = pool[pool['Team'].astype(str).str.strip() != ""].copy()
    pool = pool[pool['Team'].astype(str).str.lower() != "nan"].copy()
    pool['Position'] = pool['Position'].astype(str).str.strip().str.upper()
    pool['Position'] = pool['Position'].replace({'PK': 'K'})
    if allowed_positions is not None:
        pool = pool[pool['Position'].isin(allowed_positions)].copy()

    pool['Final_ADP'] = pd.to_numeric(pool['Final_ADP'], errors='coerce')
    pool['ADP_Avg_5way'] = pd.to_numeric(pool['ADP_Avg_5way'], errors='coerce')
    pool['ADP_15rd'] = pd.to_numeric(pool['ADP_15rd'], errors='coerce')
    pool['ADP_Combined'] = pd.to_numeric(pool['ADP_Combined'], errors='coerce')
    pool['Master_ADP'] = pd.to_numeric(pool['Master_ADP'], errors='coerce')

    # Ensure every player has an Avg ADP by falling back to the mean of available ADP sources.
    fallback_cols = ['ADP_Avg_5way', 'ADP_15rd', 'ADP_Combined', 'Master_ADP']
    pool['Avg_ADP_Resolved'] = pool[fallback_cols].mean(axis=1, skipna=True)
    pool['Avg_ADP_Resolved'] = pool['Avg_ADP_Resolved'].fillna(pool['Final_ADP'])
    pool['ADP_Resolved'] = pool['Final_ADP'].fillna(pool['Avg_ADP_Resolved'])
    pool = pool.dropna(subset=['ADP_Resolved'])

    # Collapse duplicate name variants (e.g., "Travis Etienne" vs "Travis Etienne Jr.")
    # within the same team/position to a single best source-backed row.
    pool['Name_Base'] = pool['Player'].apply(normalize_player_name)
    pool['Dup_Key'] = (
        pool['Name_Base'].astype(str).str.strip()
        + "|" + pool['Team'].astype(str).str.upper().str.strip()
        + "|" + pool['Position'].astype(str).str.upper().str.strip()
    )
    pool['Adp_Source_Count'] = pool[['Final_ADP', 'ADP_Avg_5way', 'ADP_15rd', 'ADP_Combined', 'Master_ADP']].notna().sum(axis=1)
    pool = pool.sort_values(['Dup_Key', 'Adp_Source_Count', 'ADP_Resolved'], ascending=[True, False, True])
    pool = pool.drop_duplicates(subset=['Dup_Key'], keep='first')
    pool = pool.drop(columns=['Name_Base', 'Dup_Key', 'Adp_Source_Count'])
    return pool


def get_available_targets(players_df, drafted_names, current_pick, min_options=6, base_window=2):
    pool = build_player_pool(players_df, drafted_names, ['QB', 'RB', 'WR', 'TE', 'DEF', 'K'])

    upper_bound = current_pick + base_window
    slip_lower = current_pick - 1

    base_available = pool[(pool['ADP_Resolved'] >= current_pick) & (pool['ADP_Resolved'] <= upper_bound)].copy()
    slip_adp = pool['Avg_ADP_Resolved'].fillna(pool['ADP_Resolved'])
    slipped_available = pool[
        (slip_adp >= slip_lower) &
        (slip_adp < current_pick)
    ].copy()
    available = pd.concat([base_available, slipped_available], ignore_index=True)
    available = available.drop_duplicates(subset=['Player'], keep='first')
    available['May_Not_Be_There'] = available['Avg_ADP_Resolved'].fillna(available['ADP_Resolved']) < current_pick

    while len(available) < min_options and upper_bound < current_pick + 30:
        upper_bound += 2
        base_available = pool[(pool['ADP_Resolved'] >= current_pick) & (pool['ADP_Resolved'] <= upper_bound)].copy()
        available = pd.concat([base_available, slipped_available], ignore_index=True)
        available = available.drop_duplicates(subset=['Player'], keep='first')
        available['May_Not_Be_There'] = available['Avg_ADP_Resolved'].fillna(available['ADP_Resolved']) < current_pick

    available = available.sort_values(['May_Not_Be_There', 'ADP_Resolved', 'Avg_ADP_Resolved'])
    return available, upper_bound


def get_late_round_required_targets(players_df, drafted_names, remaining_starters, remaining_flex, current_round):
    if current_round < 15:
        return None

    required_positions = [pos for pos in ["QB", "RB", "WR", "TE", "DEF", "K"] if remaining_starters[pos] > 0]
    if remaining_flex > 0:
        required_positions.extend(["RB", "WR", "TE"])
    required_positions = sorted(set(required_positions))

    if not required_positions:
        return None

    pool = build_player_pool(players_df, drafted_names, required_positions)
    return pool.sort_values('ADP_Resolved')


def calculate_final_scores(drafted_players, slot, strategy_name):
    if not drafted_players:
        return {"tier": 0.0, "value": 0.0, "adherence": 0.0, "overall": 0.0}

    # Tier score
    tier_points = 0.0
    tier_count = 0
    for p in drafted_players:
        tier = p.get("tier", np.nan)
        if pd.notna(tier):
            tier = int(tier)
            if 1 <= tier <= 5:
                tier_points += 100
            elif 6 <= tier <= 10:
                tier_points += 80
            elif 11 <= tier <= 12:
                tier_points += 60
            else:
                tier_points += 30
            tier_count += 1
    tier_score = (tier_points / max(tier_count, 1)) if tier_count > 0 else 50.0

    # Value score (how close pick was to market ADP)
    value_scores = []
    for p in drafted_players:
        adp = p.get("adp", np.nan)
        round_num = p.get("round", 1)
        pick_num = p.get("pick_number", get_pick_number(round_num, slot))
        if pd.notna(adp):
            gap = float(adp) - float(pick_num)
            value_scores.append(max(0.0, min(100.0, 100.0 - (gap * 20.0))))
    value_score = float(np.mean(value_scores)) if value_scores else 0.0

    # Strategy adherence score
    strategy_row = get_strategy_row(slot, strategy_name)
    adherence_hits = 0
    adherence_total = 0
    if strategy_row is not None:
        for p in drafted_players:
            round_num = p.get("round", 0)
            if round_num <= 0:
                continue
            col = f"Round{round_num}_Pos"
            if col in strategy_row.index and pd.notna(strategy_row[col]) and str(strategy_row[col]).strip() != "":
                expected_pos = str(strategy_row[col]).upper()
                adherence_total += 1
                if str(p.get("pos", "")).upper() == expected_pos:
                    adherence_hits += 1
    adherence_score = (adherence_hits / adherence_total * 100.0) if adherence_total > 0 else 50.0

    overall = (tier_score * 0.45) + (value_score * 0.30) + (adherence_score * 0.25)
    return {
        "tier": round(tier_score, 1),
        "value": round(value_score, 1),
        "adherence": round(adherence_score, 1),
        "overall": round(overall, 1),
    }


def get_roster_visual(drafted_players):
    counts = {"QB": 0, "RB": 0, "WR": 0, "TE": 0, "DEF": 0, "K": 0}
    for p in drafted_players:
        pos = p.get("pos")
        if pos in counts:
            counts[pos] += 1

    remaining_starters, remaining_flex, remaining_bench = get_roster_status(drafted_players)
    flex_filled = ROSTER_REQUIREMENTS["FLEX"] - remaining_flex
    bench_filled = ROSTER_REQUIREMENTS["BENCH"] - remaining_bench

    rows = []
    for pos in ["QB", "RB", "WR", "TE", "DEF", "K"]:
        rows.append({
            "Position": pos,
            "Drafted": counts[pos],
            "Needed": remaining_starters[pos],
            "Required": ROSTER_REQUIREMENTS[pos],
        })
    rows.append({"Position": "FLEX", "Drafted": flex_filled, "Needed": remaining_flex, "Required": ROSTER_REQUIREMENTS["FLEX"]})
    rows.append({"Position": "BENCH", "Drafted": bench_filled, "Needed": remaining_bench, "Required": ROSTER_REQUIREMENTS["BENCH"]})
    return pd.DataFrame(rows)


def get_strategy_summary(strategy_row):
    if strategy_row is None:
        return "Balanced best-available approach."

    positions = []
    for r in range(1, 6):
        col = f"Round{r}_Pos"
        if col in strategy_row.index and pd.notna(strategy_row[col]) and str(strategy_row[col]).strip() != "":
            positions.append(str(strategy_row[col]).upper())

    if positions:
        return f"Round plan (1-5): {' → '.join(positions)}"

    pattern = strategy_row.get("Pattern", None)
    if pd.notna(pattern) and str(pattern).strip().lower() != "generic":
        return f"Pattern focus: {pattern}"

    name = str(strategy_row.get("Strategy_Name", "")).lower()
    if "heavy-rb" in name:
        return "RB-heavy start, then fill WR depth."
    if "zero-rb" in name:
        return "WR/TE early, RB value later."
    if "hero-rb" in name:
        return "Anchor RB first, build around WR/TE."
    if "wr-heavy" in name:
        return "WR-heavy start, backfill RBs."
    if "ryans-animal" in name:
        return "Only target players from animal mascot teams."
    return "Flexible value-first strategy."


def backfill_drafted_avg_adp(drafted_players, players_df):
    lookup = players_df.set_index('Player')
    for p in drafted_players:
        name = p.get('player')
        if not name or name not in lookup.index:
            if pd.isna(p.get('avg_adp')) and pd.notna(p.get('adp')):
                p['avg_adp'] = float(p.get('adp'))
            continue

        row = lookup.loc[name]

        if pd.isna(p.get('avg_adp')):
            vals = [
                pd.to_numeric(row.get('ADP_Avg_5way'), errors='coerce'),
                pd.to_numeric(row.get('ADP_15rd'), errors='coerce'),
                pd.to_numeric(row.get('ADP_Combined'), errors='coerce'),
                pd.to_numeric(row.get('Master_ADP'), errors='coerce'),
            ]
            vals = [v for v in vals if pd.notna(v)]
            if vals:
                p['avg_adp'] = float(np.mean(vals))
            elif pd.notna(p.get('adp')):
                p['avg_adp'] = float(p.get('adp'))

        if pd.isna(p.get('tier')):
            tier_val = pd.to_numeric(row.get('Tier'), errors='coerce')
            if pd.notna(tier_val):
                p['tier'] = int(tier_val)


def _build_espn_cookie(espn_s2, swid=""):
    cookie = f"espn_s2={str(espn_s2 or '').strip()}"
    swid = str(swid or "").strip()
    if swid:
        cookie += f"; SWID={swid}"
    return cookie


def _fetch_espn_league_payload(league_id, season, espn_s2, swid="", views=None, fantasy_filter=None):
    league_id = str(league_id).strip()
    season = int(season)
    if not league_id or not str(espn_s2 or "").strip():
        return {}

    views = views or ["mTeam"]
    query = "&".join([f"view={v}" for v in views])
    url = (
        f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/"
        f"leagues/{league_id}?{query}"
    )
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Cookie": _build_espn_cookie(espn_s2, swid),
    }
    if fantasy_filter:
        headers["x-fantasy-filter"] = json.dumps(fantasy_filter)

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode())


@st.cache_data(ttl=21600, show_spinner=False)
def load_espn_season_history(league_id, season, espn_s2, swid=""):
    data = _fetch_espn_league_payload(
        league_id,
        season,
        espn_s2,
        swid,
        views=["mTeam", "mDraftDetail"],
    )

    members = {
        normalize_owner_id(m.get("id")): resolve_member_name(m)
        for m in data.get("members", [])
    }
    season_rows = []
    teams_by_id = {}
    for t in data.get("teams", []):
        owner_ids = t.get("owners") or []
        owner_id = owner_ids[0] if owner_ids else t.get("primaryOwner")
        team_id = t.get("id")
        team_name = t.get("name") or t.get("abbrev") or f"Team {team_id}"
        owner_name = resolve_manager_label(
            members.get(normalize_owner_id(owner_id), ""),
            team_name,
            team_id,
        )
        overall = (t.get("record") or {}).get("overall", {})

        team_row = {
            "season": int(season),
            "team_id": team_id,
            "team_name": team_name,
            "abbrev": t.get("abbrev", ""),
            "owner_id": owner_id,
            "owner_name": owner_name,
            "wins": overall.get("wins", 0),
            "losses": overall.get("losses", 0),
            "ties": overall.get("ties", 0),
            "points_for": overall.get("pointsFor", np.nan),
            "points_against": overall.get("pointsAgainst", np.nan),
            "final_rank": t.get("rankCalculatedFinal", t.get("rankFinal", np.nan)),
            "playoff_seed": t.get("playoffSeed", np.nan),
        }
        season_rows.append(team_row)
        teams_by_id[team_id] = team_row

    picks = data.get("draftDetail", {}).get("picks", [])
    player_ids = []
    for p in picks:
        pid = p.get("playerId")
        try:
            pid_int = int(pid)
        except Exception:
            continue
        if pid_int > 0:
            player_ids.append(pid_int)
    player_ids = sorted(set(player_ids))

    player_info_by_id = {}
    if player_ids:
        try:
            p_data = _fetch_espn_league_payload(
                league_id,
                season,
                espn_s2,
                swid,
                views=["kona_player_info"],
                fantasy_filter={"players": {"filterIds": {"value": player_ids}}},
            )
            for row in p_data.get("players", []):
                p_info = row.get("player", {})
                pid = p_info.get("id")
                name = p_info.get("fullName") or p_info.get("lastName") or p_info.get("firstName")
                pos_id = p_info.get("defaultPositionId")
                if pid is not None:
                    player_info_by_id[int(pid)] = {
                        "name": str(name).strip() if name else None,
                        "pos": ESPN_DEFAULT_POS_ID_TO_POS.get(int(pos_id)) if str(pos_id).isdigit() else None,
                    }
        except Exception:
            player_info_by_id = {}

    draft_rows = []
    sorted_picks = sorted(
        picks,
        key=lambda x: (
            int(x.get("roundId", 999) or 999),
            int(x.get("roundPickNumber", 999) or 999),
            int(x.get("overallPickNumber", 999) or 999),
        ),
    )
    for p in sorted_picks:
        team_id = p.get("teamId")
        team_row = teams_by_id.get(team_id, {})
        pid = p.get("playerId")
        try:
            pid_int = int(pid)
        except Exception:
            pid_int = -1
        lineup_slot = p.get("lineupSlotId")
        pos_from_slot = ESPN_LINEUP_SLOT_TO_POS.get(int(lineup_slot)) if str(lineup_slot).isdigit() else None
        if pid_int > 0:
            player_info = player_info_by_id.get(pid_int, {})
            player_name = player_info.get("name") or f"Player ID {pid_int}"
            player_pos = player_info.get("pos") or pos_from_slot or "—"
        else:
            player_name = "(No player recorded)"
            player_pos = pos_from_slot or "—"

        draft_rows.append(
            {
                "season": int(season),
                "team_id": team_id,
                "team_name": team_row.get("team_name", f"Team {team_id}"),
                "owner_id": team_row.get("owner_id"),
                "owner_name": team_row.get("owner_name", ""),
                "round": p.get("roundId"),
                "round_pick": p.get("roundPickNumber"),
                "overall_pick": p.get("overallPickNumber"),
                "player_id": pid_int,
                "player_name": player_name,
                "player_pos": player_pos,
                "lineup_slot_id": lineup_slot,
            }
        )

    return season_rows, draft_rows


def _render_standalone_draft_recap():
    st.title("Draft recap")
    if not st.session_state.drafted_players:
        st.info("No picks yet. Start drafting on the Draft simulator page.")
        return

    scores = calculate_final_scores(
        st.session_state.drafted_players,
        st.session_state.draft_slot or 6,
        st.session_state.strategy,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Overall", f"{scores['overall']:.0f}")
    with c2:
        st.metric("Tier quality", f"{scores['tier']:.0f}")
    with c3:
        st.metric("ADP value", f"{scores['value']:.0f}")
    with c4:
        st.metric("Strategy fit", f"{scores['adherence']:.0f}")

    st.caption(
        f"Team: {st.session_state.espn_selected_team_name or '—'} | "
        f"Slot: #{st.session_state.draft_slot or '—'} | "
        f"Strategy: {st.session_state.strategy or '—'}"
    )

    recap_df = pd.DataFrame(st.session_state.drafted_players).copy()
    recap_df = recap_df.rename(
        columns={
            "round": "Round",
            "pick_number": "Overall Pick",
            "player": "Player",
            "pos": "Position",
            "team": "Team",
            "avg_adp": "Avg ADP",
        }
    )
    show_cols = [c for c in ["Round", "Overall Pick", "Player", "Position", "Team", "Avg ADP"] if c in recap_df.columns]
    st.dataframe(recap_df[show_cols].sort_values(["Round", "Overall Pick"]), hide_index=True)


def _render_landing_page():
    st.markdown(
        """
        <div style="background:linear-gradient(120deg,#1d4ed8,#7c3aed,#db2777);padding:14px 18px;border:1px solid #7c3aed;border-radius:12px;margin-bottom:10px;">
            <div style="font-size:11px;color:#e2e8f0;font-weight:700;letter-spacing:1px;">FANTASY FOOTBALL COMMAND CENTER</div>
            <div style="font-size:24px;color:#ffffff;font-weight:800;line-height:1.2;margin-top:4px;">Welcome back</div>
            <div style="font-size:12px;color:#f1f5f9;margin-top:6px;">Use the top navigation to jump between simulator, research, league history, and draft views.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    mode = "Live ESPN connection" if st.session_state.espn_connected else "Default league fallback"
    teams_count = len(get_preferred_teams())
    picks_count = len(st.session_state.drafted_players)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("League", st.session_state.espn_league_id or DEFAULT_LEAGUE_ID)
    with m2:
        st.metric("Teams loaded", teams_count)
    with m3:
        st.metric("Draft picks made", picks_count)
    st.caption(mode)

    st.markdown("**League teams**")
    teams = get_preferred_teams()
    logo_cols = st.columns(6, gap="small")
    for i, team in enumerate(teams):
        with logo_cols[i % 6]:
            logo_url = str(team.get("logo_resolved") or team.get("logo") or "").strip()
            fallback_logo = f"https://g.espncdn.com/lm-static/ffl/images/default_logos/{(int(team.get('team_id', 1)) % 20) or 1}.svg"
            st.markdown(
                f'<div style="background:#111827;border:1px solid #334155;border-radius:10px;padding:8px;text-align:center;">'
                f'<img src="{logo_url or fallback_logo}" width="44" height="44" '
                f'onerror="this.onerror=null;this.src=\'{fallback_logo}\';" style="object-fit:contain;display:block;margin:0 auto 6px auto;">'
                f'<div style="font-size:11px;color:#e2e8f0;font-weight:600;line-height:1.2;">{team.get("abbrev") or team.get("name","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("View", key=f"landing_team_logo_{team.get('team_id', i)}", width="stretch"):
                st.session_state.team_view_team_id = team.get("team_id")
                st.session_state.app_page = "Team views"
                st.rerun()

    card_cols_top = st.columns(2, gap="small")
    with card_cols_top[0]:
        st.markdown(
            """
            <div style="background:#1d4ed8;border:1px solid #60a5fa;border-radius:10px;padding:12px 12px 10px 12px;color:#eff6ff;">
                <div style="font-weight:800;font-size:15px;">Draft simulator</div>
                <div style="font-size:12px;opacity:.95;margin-top:4px;">Run your live mock and strategy flow with pick-by-pick guidance.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open simulator", key="landing_open_sim", width="stretch"):
            st.session_state.app_page = "Draft simulator"
            st.rerun()
    with card_cols_top[1]:
        st.markdown(
            """
            <div style="background:#0ea5e9;border:1px solid #67e8f9;border-radius:10px;padding:12px 12px 10px 12px;color:#ecfeff;">
                <div style="font-weight:800;font-size:15px;">Draft research</div>
                <div style="font-size:12px;opacity:.95;margin-top:4px;">Scan sleepers, traps, and ADP board value.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open research", key="landing_open_research", width="stretch"):
            st.session_state.app_page = "Draft research"
            st.rerun()

    card_cols_bottom = st.columns(2, gap="small")
    with card_cols_bottom[0]:
        st.markdown(
            """
            <div style="background:#f59e0b;border:1px solid #fde68a;border-radius:10px;padding:12px 12px 10px 12px;color:#1f2937;">
                <div style="font-weight:800;font-size:15px;">League history</div>
                <div style="font-size:12px;opacity:.95;margin-top:4px;">Compare season outcomes across selected years.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open league history", key="landing_open_league", width="stretch"):
            st.session_state.app_page = "League history"
            st.rerun()
    with card_cols_bottom[1]:
        st.markdown(
            """
            <div style="background:#ef4444;border:1px solid #fca5a5;border-radius:10px;padding:12px 12px 10px 12px;color:#fff1f2;">
                <div style="font-weight:800;font-size:15px;">Draft view</div>
                <div style="font-size:12px;opacity:.95;margin-top:4px;">Inspect each team’s prior drafts and pick facts by season.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open draft view", key="landing_open_team_views", width="stretch"):
            st.session_state.app_page = "Team views"
            st.rerun()


def _render_draft_research_page():
    st.title("Draft research")
    if st.button("Back to home", key="research_back_home"):
        st.session_state.app_page = "Landing"
        st.rerun()

    st.subheader("Top sleepers")
    st.dataframe(df_sleepers.head(25), hide_index=True)
    st.subheader("Top trap picks")
    st.dataframe(df_traps.head(25), hide_index=True)

    pool = build_player_pool(df_players, drafted_names=set(), allowed_positions=["QB", "RB", "WR", "TE", "DEF", "K"])
    pool = pool.sort_values("ADP_Resolved")
    show_cols = [c for c in ["Player", "Position", "Team", "ADP_Resolved", "Avg_ADP_Resolved", "Tier"] if c in pool.columns]
    st.subheader("ADP board")
    st.dataframe(pool[show_cols].head(150), hide_index=True)


def _default_season_selection():
    cy = datetime.now().year
    return [s for s in [2023, 2024, 2025] if 2018 <= s <= cy]


def _default_team_view_season_selection():
    return _default_season_selection()


def _ensure_season_multiselect_default(key, desired_defaults):
    desired = sorted(set(int(s) for s in desired_defaults))
    current = st.session_state.get(key)
    if current is None:
        st.session_state[key] = desired
        return
    try:
        current_norm = sorted(set(int(s) for s in current))
    except Exception:
        st.session_state[key] = desired
        return

    # Migrate old default selection (2024, 2025, 2026) to new default (2023, 2024, 2025).
    old_default = sorted([s for s in [2024, 2025, 2026] if 2018 <= s <= datetime.now().year])
    if current_norm == old_default:
        st.session_state[key] = desired


def _build_fallback_league_rows(seasons):
    rows = []
    for season in seasons:
        for t in get_preferred_teams():
            rows.append(
                {
                    "season": int(season),
                    "team_name": t.get("name", f"Team {t.get('team_id', '')}"),
                    "owner_name": t.get("owner") or "Manager unavailable",
                    "record": "—",
                    "points_for": np.nan,
                    "points_against": np.nan,
                    "final_rank": np.nan,
                    "playoff_seed": np.nan,
                    "data_source": "Default fallback",
                }
            )
    return rows


def _build_fallback_team_rows(selected_team, seasons):
    owner_name = normalize_manager_name(selected_team.get("owner"))
    rows = []
    for season in seasons:
        rows.append(
            {
                "season": int(season),
                "team_name": selected_team.get("name", f"Team {selected_team.get('team_id', '')}"),
                "owner_name": owner_name,
                "record": "—",
                "points_for": np.nan,
                "points_against": np.nan,
                "final_rank": np.nan,
                "playoff_seed": np.nan,
                "wins": np.nan,
                "losses": np.nan,
                "ties": np.nan,
                "data_source": "Default fallback",
            }
        )
    return rows


def _build_fallback_draft_rows(selected_team, season):
    owner_name = normalize_manager_name(selected_team.get("owner"))
    team_name = selected_team.get("name", f"Team {selected_team.get('team_id', '')}")
    rows = []
    for rnd in range(1, 17):
        rows.append(
            {
                "round": rnd,
                "round_pick": np.nan,
                "overall_pick": np.nan,
                "player_name": "(No live draft pick data)",
                "player_pos": "—",
                "team_name": team_name,
                "owner_name": owner_name,
                "source": "Default fallback",
                "season": int(season),
            }
        )
    return rows


def _render_league_history_page():
    st.title("League history")
    if st.button("Back to home", key="league_back_home"):
        st.session_state.app_page = "Landing"
        st.rerun()

    cy = datetime.now().year
    season_options = list(range(cy, 2017, -1))
    _ensure_season_multiselect_default("league_hist_seasons", _default_season_selection())
    selected_seasons = st.multiselect(
        "Seasons",
        options=season_options,
        default=_default_season_selection(),
        key="league_hist_seasons",
    )
    if not selected_seasons:
        selected_seasons = _default_season_selection()
    seasons = sorted(set(int(s) for s in selected_seasons))

    season_rows = []
    failed_seasons = []
    if st.session_state.espn_s2:
        with st.spinner("Loading league history..."):
            for season in seasons:
                try:
                    s_rows, _ = load_espn_season_history(
                        st.session_state.espn_league_id,
                        season,
                        st.session_state.espn_s2,
                        st.session_state.espn_swid,
                    )
                    season_rows.extend(s_rows)
                except urllib.error.HTTPError as e:
                    failed_seasons.append(f"{season} (HTTP {e.code})")
                except Exception:
                    failed_seasons.append(f"{season} (failed)")
    else:
        failed_seasons = [f"{season} (no live connection)" for season in seasons]

    if failed_seasons:
        st.warning("Some seasons could not be loaded: " + ", ".join(failed_seasons))

    if season_rows:
        season_df = pd.DataFrame(season_rows)
        loaded_seasons = {int(s) for s in season_df["season"].dropna().tolist()}
    else:
        season_df = pd.DataFrame()
        loaded_seasons = set()

    missing_seasons = [s for s in seasons if s not in loaded_seasons]
    if missing_seasons:
        season_df = pd.concat(
            [season_df, pd.DataFrame(_build_fallback_league_rows(missing_seasons))],
            ignore_index=True,
            sort=False,
        )

    if season_df.empty:
        season_df = pd.DataFrame(_build_fallback_league_rows(seasons))

    if "record" not in season_df.columns:
        season_df["record"] = (
            season_df.get("wins", pd.Series(["—"] * len(season_df))).fillna("—").astype(str)
            + "-"
            + season_df.get("losses", pd.Series(["—"] * len(season_df))).fillna("—").astype(str)
            + "-"
            + season_df.get("ties", pd.Series(["—"] * len(season_df))).fillna("—").astype(str)
        )
    canonical_owner_by_id = {
        normalize_owner_id(t.get("owner_id")): normalize_manager_name(t.get("owner"))
        for t in get_preferred_teams()
    }
    season_df["owner_name"] = season_df.apply(
        lambda r: _merge_manager_name(
            r.get("owner_name", ""),
            r.get("owner_id"),
            canonical_owner_by_id,
            r.get("team_name", ""),
            r.get("team_id"),
        ),
        axis=1,
    )
    season_df["data_source"] = season_df.get("data_source", "Live ESPN")
    season_df["wins_num"] = pd.to_numeric(season_df.get("wins"), errors="coerce").fillna(0)
    season_df["losses_num"] = pd.to_numeric(season_df.get("losses"), errors="coerce").fillna(0)
    season_df["ties_num"] = pd.to_numeric(season_df.get("ties"), errors="coerce").fillna(0)
    season_df["points_for_num"] = pd.to_numeric(season_df.get("points_for"), errors="coerce").fillna(0)
    season_df["points_against_num"] = pd.to_numeric(season_df.get("points_against"), errors="coerce").fillna(0)
    season_df["final_rank_num"] = pd.to_numeric(season_df.get("final_rank"), errors="coerce")
    season_df.loc[season_df["final_rank_num"] <= 0, "final_rank_num"] = np.nan
    season_df["record"] = (
        season_df["wins_num"].astype(int).astype(str)
        + "-"
        + season_df["losses_num"].astype(int).astype(str)
        + "-"
        + season_df["ties_num"].astype(int).astype(str)
    )

    sort_map = {
        "Season": "season",
        "Team": "team_name",
        "Manager": "owner_name",
        "Points For": "points_for_num",
        "Points Against": "points_against_num",
        "Final Rank": "final_rank_num",
    }
    s1, s2 = st.columns([2, 1])
    with s1:
        sort_by = st.selectbox("Sort by", list(sort_map.keys()), index=0, key="league_history_sort_by")
    with s2:
        sort_order = st.selectbox("Order", ["Descending", "Ascending"], index=0, key="league_history_sort_order")

    season_df = season_df.sort_values(
        sort_map[sort_by],
        ascending=(sort_order == "Ascending"),
        na_position="last",
    )
    show_cols = [
        "season", "team_name", "owner_name", "record", "points_for",
        "points_against", "final_rank", "playoff_seed", "data_source",
    ]
    st.dataframe(
        season_df[show_cols].rename(
            columns={
                "season": "Season",
                "team_name": "Team",
                "owner_name": "Manager",
                "record": "Record",
                "points_for": "Points For",
                "points_against": "Points Against",
                "final_rank": "Final Rank",
                "playoff_seed": "Seed",
                "data_source": "Source",
            }
        ),
        hide_index=True,
    )

    st.subheader("League trends by year (all managers)")
    league_trend = (
        season_df.groupby(["season", "owner_name"], as_index=False)
        .agg(
            wins_num=("wins_num", "sum"),
            losses_num=("losses_num", "sum"),
            points_for_num=("points_for_num", "sum"),
            points_against_num=("points_against_num", "sum"),
        )
        .sort_values(["season", "owner_name"])
    )
    if not league_trend.empty:
        wins_pivot = league_trend.pivot(index="season", columns="owner_name", values="wins_num").sort_index()
        losses_pivot = league_trend.pivot(index="season", columns="owner_name", values="losses_num").sort_index()
        pf_pivot = league_trend.pivot(index="season", columns="owner_name", values="points_for_num").sort_index()
        pa_pivot = league_trend.pivot(index="season", columns="owner_name", values="points_against_num").sort_index()

        c1, c2 = st.columns(2)
        with c1:
            st.caption("Wins")
            st.line_chart(wins_pivot)
            st.caption("Points for")
            st.line_chart(pf_pivot)
        with c2:
            st.caption("Losses")
            st.line_chart(losses_pivot)
            st.caption("Points against")
            st.line_chart(pa_pivot)

    st.subheader("All-time manager totals")
    latest_team_by_manager = (
        season_df.sort_values(["owner_name", "season"], ascending=[True, False])
        .drop_duplicates(subset=["owner_name"], keep="first")[["owner_name", "team_name"]]
        .rename(columns={"team_name": "Current_Team"})
    )
    totals_df = (
        season_df.groupby(["owner_name"], as_index=False)
        .agg(
            Seasons=("season", "nunique"),
            Wins=("wins_num", "sum"),
            Losses=("losses_num", "sum"),
            Ties=("ties_num", "sum"),
            Points_For=("points_for_num", "sum"),
            Points_Against=("points_against_num", "sum"),
        )
    )
    totals_df = totals_df.merge(latest_team_by_manager, on="owner_name", how="left")
    totals_df["Record"] = (
        totals_df["Wins"].astype(int).astype(str)
        + "-"
        + totals_df["Losses"].astype(int).astype(str)
        + "-"
        + totals_df["Ties"].astype(int).astype(str)
    )
    totals_df["Point_Diff"] = totals_df["Points_For"] - totals_df["Points_Against"]
    totals_df = totals_df.sort_values(["Points_For", "Point_Diff"], ascending=[False, False])
    st.dataframe(
        totals_df.rename(
            columns={
                "owner_name": "Manager",
                "Current_Team": "Current Team",
                "Points_For": "Points For",
                "Points_Against": "Points Against",
                "Point_Diff": "Point Diff",
            }
        )[
            ["Manager", "Current Team", "Seasons", "Record", "Wins", "Losses", "Ties", "Points For", "Points Against", "Point Diff"]
        ],
        hide_index=True,
    )

    st.subheader("Season winners and runner-up")
    winners_rows = []
    for season in sorted(season_df["season"].dropna().astype(int).unique(), reverse=True):
        s_df = season_df[season_df["season"] == season].copy()
        ranked = s_df[s_df["final_rank_num"].notna()].sort_values("final_rank_num")
        champ = ranked[ranked["final_rank_num"] == 1].head(1)
        if champ.empty:
            champ = ranked.head(1)
        runner = ranked[ranked["final_rank_num"] == 2].head(1)
        if runner.empty:
            runner = ranked.iloc[1:2] if len(ranked) > 1 else pd.DataFrame()

        winners_rows.append(
            {
                "Season": season,
                "Winner": champ.iloc[0]["team_name"] if not champ.empty else "—",
                "Winner Manager": champ.iloc[0]["owner_name"] if not champ.empty else "—",
                "Winner Record": champ.iloc[0]["record"] if not champ.empty else "—",
                "2nd Place": runner.iloc[0]["team_name"] if not runner.empty else "—",
                "2nd Manager": runner.iloc[0]["owner_name"] if not runner.empty else "—",
                "2nd Record": runner.iloc[0]["record"] if not runner.empty else "—",
            }
        )
    st.dataframe(pd.DataFrame(winners_rows), hide_index=True)


def _render_profiles_page():
    st.title("Profiles")
    st.caption("Draft tendencies, outcomes, and correlation signals across selected seasons.")

    cy = datetime.now().year
    season_options = list(range(cy, 2017, -1))
    _ensure_season_multiselect_default("profiles_seasons", _default_season_selection())
    selected_seasons = st.multiselect(
        "Seasons",
        options=season_options,
        default=_default_season_selection(),
        key="profiles_seasons",
    )
    if not selected_seasons:
        selected_seasons = _default_season_selection()
    seasons = sorted(set(int(s) for s in selected_seasons))

    season_rows = []
    draft_rows = []
    failed_seasons = []
    if st.session_state.espn_s2:
        with st.spinner("Loading profile data..."):
            for season in seasons:
                try:
                    s_rows, d_rows = load_espn_season_history(
                        st.session_state.espn_league_id,
                        season,
                        st.session_state.espn_s2,
                        st.session_state.espn_swid,
                    )
                    season_rows.extend(s_rows)
                    draft_rows.extend(d_rows)
                except urllib.error.HTTPError as e:
                    failed_seasons.append(f"{season} (HTTP {e.code})")
                except Exception:
                    failed_seasons.append(f"{season} (failed)")
    else:
        failed_seasons = [f"{season} (no live connection)" for season in seasons]

    if failed_seasons:
        st.warning("Some seasons could not be loaded: " + ", ".join(failed_seasons))

    season_df = pd.DataFrame(season_rows) if season_rows else pd.DataFrame(_build_fallback_league_rows(seasons))
    draft_df = pd.DataFrame(draft_rows)
    if draft_df.empty:
        fallback_drafts = []
        for season in seasons:
            for t in get_preferred_teams():
                fallback_drafts.extend(_build_fallback_draft_rows(t, season))
        draft_df = pd.DataFrame(fallback_drafts)

    canonical_owner_by_id = {
        normalize_owner_id(t.get("owner_id")): normalize_manager_name(t.get("owner"))
        for t in get_preferred_teams()
    }
    season_df["owner_name"] = season_df.apply(
        lambda r: _merge_manager_name(
            r.get("owner_name", ""),
            r.get("owner_id"),
            canonical_owner_by_id,
            r.get("team_name", ""),
            r.get("team_id"),
        ),
        axis=1,
    )
    draft_df["owner_name"] = draft_df.apply(
        lambda r: _merge_manager_name(
            r.get("owner_name", ""),
            r.get("owner_id"),
            canonical_owner_by_id,
            r.get("team_name", ""),
            r.get("team_id"),
        ),
        axis=1,
    )
    draft_df["player_pos"] = draft_df.get("player_pos", "—").fillna("—").astype(str).str.upper()
    draft_df["round"] = pd.to_numeric(draft_df.get("round"), errors="coerce")
    draft_df["round_pick"] = pd.to_numeric(draft_df.get("round_pick"), errors="coerce")
    draft_df["overall_pick"] = pd.to_numeric(draft_df.get("overall_pick"), errors="coerce")

    season_df["wins_num"] = pd.to_numeric(season_df.get("wins"), errors="coerce").fillna(0)
    season_df["losses_num"] = pd.to_numeric(season_df.get("losses"), errors="coerce").fillna(0)
    season_df["ties_num"] = pd.to_numeric(season_df.get("ties"), errors="coerce").fillna(0)
    season_df["points_for_num"] = pd.to_numeric(season_df.get("points_for"), errors="coerce").fillna(0)
    season_df["points_against_num"] = pd.to_numeric(season_df.get("points_against"), errors="coerce").fillna(0)
    season_df["final_rank_num"] = pd.to_numeric(season_df.get("final_rank"), errors="coerce")
    season_df["record"] = (
        season_df["wins_num"].astype(int).astype(str)
        + "-"
        + season_df["losses_num"].astype(int).astype(str)
        + "-"
        + season_df["ties_num"].astype(int).astype(str)
    )

    profile_rows = []
    for _, srow in season_df.iterrows():
        season = int(srow.get("season"))
        team_id = srow.get("team_id")
        manager = srow.get("owner_name", "Unknown manager")
        team_name = srow.get("team_name", "Team")
        picks = draft_df[(draft_df["season"] == season) & (draft_df["team_id"] == team_id)].copy()
        if picks.empty:
            picks = draft_df[
                (draft_df["season"] == season)
                & (draft_df["owner_name"].astype(str).str.lower() == str(manager).lower())
            ].copy()
        picks = picks.sort_values(["round", "round_pick", "overall_pick"])
        first5 = picks[picks["round"] <= 5]["player_pos"].head(5).tolist()
        first8 = picks[picks["round"] <= 8]["player_pos"].tolist()
        pos_counts = pd.Series(first8).value_counts() if first8 else pd.Series(dtype="int64")
        profile_rows.append(
            {
                "Season": season,
                "Manager": manager,
                "Team": team_name,
                "Round1-5 Pos": " | ".join(first5) if first5 else "—",
                "Inferred Strategy": infer_draft_strategy_label(first5),
                "QB_First8": int(pos_counts.get("QB", 0)),
                "RB_First8": int(pos_counts.get("RB", 0)),
                "WR_First8": int(pos_counts.get("WR", 0)),
                "TE_First8": int(pos_counts.get("TE", 0)),
                "DEF_First8": int(pos_counts.get("DEF", 0)),
                "K_First8": int(pos_counts.get("K", 0)),
                "Record": srow.get("record", "—"),
                "Final Rank": srow.get("final_rank_num", np.nan),
                "Points For": srow.get("points_for_num", 0),
                "Points Against": srow.get("points_against_num", 0),
                "Wins": srow.get("wins_num", 0),
                "Losses": srow.get("losses_num", 0),
            }
        )
    profiles_df = pd.DataFrame(profile_rows)
    profiles_df = profiles_df.sort_values(["Season", "Manager"], ascending=[False, True])

    manager_filter = st.multiselect(
        "Filter managers",
        options=sorted(profiles_df["Manager"].dropna().astype(str).unique().tolist()),
        default=[],
        key="profiles_manager_filter",
    )

    filtered_profiles_df = profiles_df.copy()
    if manager_filter:
        filtered_profiles_df = filtered_profiles_df[filtered_profiles_df["Manager"].isin(manager_filter)].copy()

    st.subheader("Draft strategy profiles")
    st.dataframe(filtered_profiles_df, hide_index=True)

    st.subheader("Manager 3-year summaries")
    manager_summary = (
        filtered_profiles_df.groupby("Manager", as_index=False)
        .agg(
            Seasons=("Season", "nunique"),
            Avg_Final_Rank=("Final Rank", "mean"),
            Total_Wins=("Wins", "sum"),
            Total_Losses=("Losses", "sum"),
            Total_Points_For=("Points For", "sum"),
            Total_Points_Against=("Points Against", "sum"),
        )
        .sort_values(["Total_Points_For", "Total_Wins"], ascending=[False, False])
    )
    st.dataframe(manager_summary, hide_index=True)

    st.subheader("Draft vs outcome correlation (selected seasons)")
    st.caption("Positive = linked to better finish. Negative = linked to worse finish. Near 0 = weak signal.")
    corr_df = filtered_profiles_df.copy()
    corr_df["Final Rank"] = pd.to_numeric(corr_df["Final Rank"], errors="coerce")
    corr_df = corr_df[corr_df["Final Rank"].notna()].copy()
    if len(corr_df) >= 3:
        max_rank = float(corr_df["Final Rank"].max())
        corr_df["Outcome Score"] = (max_rank + 1) - corr_df["Final Rank"]
        feature_cols = [
            "QB_First8", "RB_First8", "WR_First8", "TE_First8", "DEF_First8", "K_First8",
            "Points For", "Points Against", "Wins", "Losses",
        ]
        feature_labels = {
            "QB_First8": "QBs drafted in first 8 picks",
            "RB_First8": "RBs drafted in first 8 picks",
            "WR_First8": "WRs drafted in first 8 picks",
            "TE_First8": "TEs drafted in first 8 picks",
            "DEF_First8": "DEF drafted in first 8 picks",
            "K_First8": "K drafted in first 8 picks",
            "Points For": "Season points for",
            "Points Against": "Season points against",
            "Wins": "Season wins",
            "Losses": "Season losses",
        }
        corr_rows = []
        for feature in feature_cols:
            series = pd.to_numeric(corr_df[feature], errors="coerce")
            if series.nunique(dropna=True) < 2:
                continue
            corr_val = series.corr(corr_df["Outcome Score"])
            if pd.notna(corr_val):
                abs_corr = abs(float(corr_val))
                if abs_corr >= 0.6:
                    strength = "Strong"
                elif abs_corr >= 0.35:
                    strength = "Moderate"
                elif abs_corr >= 0.15:
                    strength = "Light"
                else:
                    strength = "Very light"
                corr_rows.append(
                    {
                        "Metric": feature_labels.get(feature, feature),
                        "Correlation": round(float(corr_val), 3),
                        "Direction": "Better finish" if corr_val > 0 else "Worse finish",
                        "Signal Strength": strength,
                    }
                )
        corr_out = pd.DataFrame(corr_rows).sort_values(
            "Correlation",
            key=lambda s: s.abs(),
            ascending=False,
        )
        st.dataframe(corr_out, hide_index=True)
    else:
        st.info("Not enough completed season rows (need at least 3) to calculate correlation.")


def _render_team_views_hub():
    st.title("Draft view")

    teams = get_preferred_teams()
    if not teams:
        st.info("No teams available.")
        return

    with st.expander("Choose your team", expanded=False):
        cols = st.columns(3)
        for i, team in enumerate(teams):
            team_name = str(team.get("name") or f"Team {team.get('team_id')}")
            label = f"{team_name} • {get_team_manager_display(team)}"
            with cols[i % 3]:
                if st.button(label, key=f"team_view_btn_{team.get('team_id', i)}", width="stretch"):
                    st.session_state.team_view_team_id = team.get("team_id")
                    st.rerun()

    selected = None
    if st.session_state.team_view_team_id is not None:
        for team in teams:
            if team.get("team_id") == st.session_state.team_view_team_id:
                selected = team
                break
    if selected is None:
        selected = teams[0]

    st.divider()
    _render_team_history_page(preselected_team=selected)


def _render_team_history_page(preselected_team=None):
    title_name = preselected_team.get("name") if isinstance(preselected_team, dict) else None
    st.title(f"Draft view: {title_name}" if title_name else "Draft view")

    current_teams = get_preferred_teams()
    if not current_teams:
        st.warning("No league teams available.")
        return

    options = []
    option_map = {}
    for t in current_teams:
        owner_name = t.get("owner") or "Unknown owner"
        label = f"{t.get('name', 'Team')} • {owner_name}"
        options.append(label)
        option_map[label] = t

    if preselected_team is not None:
        selected_team = preselected_team
    else:
        default_index = 0
        for i, label in enumerate(options):
            t = option_map[label]
            if (
                st.session_state.espn_selected_owner_id is not None
                and t.get("owner_id") == st.session_state.espn_selected_owner_id
            ):
                default_index = i
                break
            if (
                st.session_state.espn_selected_owner_id is None
                and st.session_state.espn_selected_team_id is not None
                and t.get("team_id") == st.session_state.espn_selected_team_id
            ):
                default_index = i
                break
        selected_label = st.selectbox("Choose a team/manager", options, index=default_index, key="team_history_selector")
        selected_team = option_map[selected_label]
    selected_owner_id = selected_team.get("owner_id")
    selected_owner_name = get_team_manager_display(selected_team)

    cy = datetime.now().year
    season_options = list(range(cy, 2017, -1))
    season_key = f"team_hist_seasons_{selected_team.get('team_id', 'default')}"
    _ensure_season_multiselect_default(season_key, _default_team_view_season_selection())
    selected_seasons = st.multiselect(
        "Seasons",
        options=season_options,
        default=_default_team_view_season_selection(),
        key=season_key,
    )
    if not selected_seasons:
        selected_seasons = _default_team_view_season_selection()
    seasons = sorted(set(int(s) for s in selected_seasons))

    season_rows = []
    draft_rows = []
    failed_seasons = []
    if st.session_state.espn_s2:
        with st.spinner("Loading season history..."):
            for season in seasons:
                try:
                    s_rows, d_rows = load_espn_season_history(
                        st.session_state.espn_league_id,
                        season,
                        st.session_state.espn_s2,
                        st.session_state.espn_swid,
                    )
                    season_rows.extend(s_rows)
                    draft_rows.extend(d_rows)
                except urllib.error.HTTPError as e:
                    failed_seasons.append(f"{season} (HTTP {e.code})")
                except Exception:
                    failed_seasons.append(f"{season} (failed)")
    else:
        failed_seasons = [f"{season} (no live connection)" for season in seasons]

    if failed_seasons:
        st.warning("Some seasons could not be loaded: " + ", ".join(failed_seasons))

    if season_rows:
        season_df = pd.DataFrame(season_rows)
    else:
        season_df = pd.DataFrame()
    draft_df = pd.DataFrame(draft_rows)

    canonical_owner_by_id = {
        normalize_owner_id(t.get("owner_id")): normalize_manager_name(t.get("owner"))
        for t in get_preferred_teams()
    }
    if not season_df.empty:
        season_df["owner_name"] = season_df.apply(
            lambda r: _merge_manager_name(
                r.get("owner_name", ""),
                r.get("owner_id"),
                canonical_owner_by_id,
                r.get("team_name", ""),
                r.get("team_id"),
            ),
            axis=1,
        )
    if not draft_df.empty:
        draft_df["owner_name"] = draft_df.apply(
            lambda r: _merge_manager_name(
                r.get("owner_name", ""),
                r.get("owner_id"),
                canonical_owner_by_id,
                r.get("team_name", ""),
                r.get("team_id"),
            ),
            axis=1,
        )
        draft_df["source"] = "Live ESPN"

    selected_team_id = selected_team.get("team_id")
    if not season_df.empty and selected_team_id is not None:
        team_history_df = season_df[season_df["team_id"] == selected_team_id].copy()
    elif not season_df.empty and selected_owner_id is not None:
        selected_owner_norm = normalize_owner_id(selected_owner_id)
        owner_norm_series = season_df["owner_id"].apply(normalize_owner_id)
        team_history_df = season_df[owner_norm_series == selected_owner_norm].copy()
    elif not season_df.empty:
        team_history_df = season_df[
            season_df["owner_name"].astype(str).str.lower() == str(selected_owner_name).lower()
        ].copy()
    else:
        team_history_df = pd.DataFrame()

    if team_history_df.empty:
        team_history_df = pd.DataFrame(_build_fallback_team_rows(selected_team, seasons))
        st.info("Showing default fallback history for selected seasons.")

    team_history_df = team_history_df.sort_values("season", ascending=False)
    if "data_source" in team_history_df.columns:
        team_history_df["_src_priority"] = team_history_df["data_source"].astype(str).eq("Live ESPN").astype(int)
        team_history_df = team_history_df.sort_values(["season", "_src_priority"], ascending=[False, False])
    team_history_df = team_history_df.drop_duplicates(subset=["season"], keep="first")
    if "record" not in team_history_df.columns:
        team_history_df["record"] = (
            team_history_df.get("wins", pd.Series(["—"] * len(team_history_df))).fillna("—").astype(str)
            + "-"
            + team_history_df.get("losses", pd.Series(["—"] * len(team_history_df))).fillna("—").astype(str)
            + "-"
            + team_history_df.get("ties", pd.Series(["—"] * len(team_history_df))).fillna("—").astype(str)
        )
    team_history_df["owner_name"] = team_history_df["owner_name"].apply(normalize_manager_name)
    team_history_df["data_source"] = team_history_df.get("data_source", "Live ESPN")
    if "_src_priority" in team_history_df.columns:
        team_history_df = team_history_df.drop(columns=["_src_priority"])

    st.subheader("Season performance")
    perf_cols = [
        "season",
        "team_name",
        "owner_name",
        "record",
        "points_for",
        "points_against",
        "final_rank",
        "playoff_seed",
        "data_source",
    ]
    st.dataframe(
        team_history_df[perf_cols].rename(
            columns={
                "season": "Season",
                "team_name": "Team Name",
                "owner_name": "Manager",
                "record": "Record",
                "points_for": "Points For",
                "points_against": "Points Against",
                "final_rank": "Final Rank",
                "playoff_seed": "Seed",
                "data_source": "Source",
            }
        ),
        hide_index=True,
    )

    st.subheader("Team trends by year")
    trend_df = team_history_df.copy()
    trend_df["wins_num"] = pd.to_numeric(trend_df.get("wins"), errors="coerce").fillna(0)
    trend_df["losses_num"] = pd.to_numeric(trend_df.get("losses"), errors="coerce").fillna(0)
    trend_df["points_for_num"] = pd.to_numeric(trend_df.get("points_for"), errors="coerce").fillna(0)
    trend_df["points_against_num"] = pd.to_numeric(trend_df.get("points_against"), errors="coerce").fillna(0)
    trend_df = trend_df.sort_values("season")
    trend_plot = trend_df.set_index("season")
    t1, t2 = st.columns(2)
    with t1:
        st.caption("Wins")
        st.line_chart(trend_plot[["wins_num"]].rename(columns={"wins_num": "Wins"}))
        st.caption("Points for")
        st.line_chart(trend_plot[["points_for_num"]].rename(columns={"points_for_num": "Points For"}))
    with t2:
        st.caption("Losses")
        st.line_chart(trend_plot[["losses_num"]].rename(columns={"losses_num": "Losses"}))
        st.caption("Points against")
        st.line_chart(trend_plot[["points_against_num"]].rename(columns={"points_against_num": "Points Against"}))
    total_wins = pd.to_numeric(team_history_df.get("wins"), errors="coerce").fillna(0).sum()
    total_losses = pd.to_numeric(team_history_df.get("losses"), errors="coerce").fillna(0).sum()
    total_ties = pd.to_numeric(team_history_df.get("ties"), errors="coerce").fillna(0).sum()
    total_pf = pd.to_numeric(team_history_df.get("points_for"), errors="coerce").fillna(0).sum()
    total_pa = pd.to_numeric(team_history_df.get("points_against"), errors="coerce").fillna(0).sum()

    t1, t2, t3 = st.columns(3)
    with t1:
        st.metric("Total record", f"{int(total_wins)}-{int(total_losses)}-{int(total_ties)}")
    with t2:
        st.metric("Total points for", f"{total_pf:.1f}")
    with t3:
        st.metric("Total points against", f"{total_pa:.1f}")

    st.subheader("Draft by year")
    seasons_for_drafts = sorted({int(s) for s in team_history_df["season"].dropna().tolist()}, reverse=True)
    season_row_lookup = {int(r["season"]): r for _, r in team_history_df.iterrows() if pd.notna(r.get("season"))}
    picks_by_season = {}
    for season in seasons_for_drafts:
        row = season_row_lookup.get(season, {})
        if selected_team_id is not None and not draft_df.empty:
            year_picks = draft_df[
                (draft_df["season"] == season)
                & (draft_df["team_id"] == selected_team_id)
            ].copy()
        elif selected_owner_id is not None and not draft_df.empty:
            selected_owner_norm = normalize_owner_id(selected_owner_id)
            year_picks = draft_df[
                (draft_df["season"] == season)
                & (draft_df["owner_id"].apply(normalize_owner_id) == selected_owner_norm)
            ].copy()
        elif not draft_df.empty:
            year_picks = draft_df[
                (draft_df["season"] == season)
                & (draft_df["owner_name"].astype(str).str.lower() == str(selected_owner_name).lower())
            ].copy()
        else:
            year_picks = pd.DataFrame()
        year_picks = year_picks.sort_values(["round", "round_pick", "overall_pick"])
        picks_by_season[season] = year_picks.copy()

    facts_rows = []
    for season in seasons_for_drafts:
        year_picks = picks_by_season.get(season, pd.DataFrame()).copy()
        if year_picks.empty:
            year_picks = pd.DataFrame(_build_fallback_draft_rows(selected_team, season))
        overall = pd.to_numeric(year_picks.get("overall_pick"), errors="coerce")
        known_players = year_picks["player_name"].astype(str) != "(No live draft pick data)"
        first_three = ", ".join(year_picks.head(3)["player_name"].astype(str).tolist())
        facts_rows.append(
            {
                "Season": season,
                "Manager": get_team_manager_display(selected_team),
                "Total Picks": int(len(year_picks)),
                "Named Picks": int(known_players.sum()),
                "First Overall Pick": int(overall.min()) if overall.notna().any() else "—",
                "Avg Overall Pick": round(float(overall.mean()), 1) if overall.notna().any() else "—",
                "First 3 Picks": first_three if first_three else "—",
            }
        )
    st.subheader("Basic pick facts")
    st.dataframe(pd.DataFrame(facts_rows), hide_index=True)

    for season in seasons_for_drafts:
        row = season_row_lookup.get(season, {})
        year_picks = picks_by_season.get(season, pd.DataFrame()).copy()
        wins = row.get("wins")
        losses = row.get("losses")
        ties = row.get("ties")
        if pd.notna(wins) and pd.notna(losses) and pd.notna(ties):
            rec_text = f"{int(wins)}-{int(losses)}-{int(ties)}"
        else:
            rec_text = "—"
        team_label = row.get("team_name", selected_team.get("name", "Team"))
        with st.expander(f"{season} • {team_label} ({rec_text})", expanded=False):
            if year_picks.empty:
                year_picks = pd.DataFrame(_build_fallback_draft_rows(selected_team, season))
                st.caption("Showing default fallback draft rounds.")
            year_picks["source"] = year_picks.get("source", "Live ESPN")
            year_picks["team_name"] = year_picks.get("team_name", team_label)
            year_picks["owner_name"] = year_picks.get("owner_name", selected_owner_name)
            st.dataframe(
                year_picks[["round", "round_pick", "overall_pick", "player_name", "team_name", "owner_name", "source"]].rename(
                    columns={
                        "round": "Round",
                        "round_pick": "Pick in Round",
                        "overall_pick": "Overall Pick",
                        "player_name": "Player",
                        "team_name": "Fantasy Team",
                        "owner_name": "Manager",
                        "source": "Source",
                    }
                ),
                hide_index=True,
            )


def sync_espn_connection():
    if not st.session_state.espn_s2 or not st.session_state.espn_league_id:
        st.session_state.espn_connected = False
        st.session_state.espn_connect_status = "Live ESPN unavailable. Using default league data."
        if not st.session_state.espn_teams_cache:
            st.session_state.espn_teams_cache = DEFAULT_LEAGUE_TEAMS.copy()
        return st.session_state.espn_teams_cache

    load_espn_league_teams.clear()
    try:
        teams = load_espn_league_teams(
            st.session_state.espn_league_id,
            2026,
            st.session_state.espn_s2,
            st.session_state.espn_swid,
        )
        if teams:
            st.session_state.espn_connected = True
            st.session_state.espn_connect_status = (
                f"Connected to league {st.session_state.espn_league_id} ({len(teams)} teams)."
            )
            st.session_state.espn_teams_cache = teams
            return teams
        st.session_state.espn_connected = False
        st.session_state.espn_connect_status = "Connection failed. Using default league data."
        if not st.session_state.espn_teams_cache:
            st.session_state.espn_teams_cache = DEFAULT_LEAGUE_TEAMS.copy()
        return st.session_state.espn_teams_cache
    except urllib.error.HTTPError as e:
        st.session_state.espn_connected = False
        st.session_state.espn_connect_status = f"Connection failed (HTTP {e.code}). Using default league data."
        if not st.session_state.espn_teams_cache:
            st.session_state.espn_teams_cache = DEFAULT_LEAGUE_TEAMS.copy()
        return st.session_state.espn_teams_cache
    except Exception:
        st.session_state.espn_connected = False
        st.session_state.espn_connect_status = "Connection failed. Using default league data."
        if not st.session_state.espn_teams_cache:
            st.session_state.espn_teams_cache = DEFAULT_LEAGUE_TEAMS.copy()
        return st.session_state.espn_teams_cache


def get_preferred_teams():
    teams = st.session_state.espn_teams_cache if st.session_state.espn_teams_cache else []
    if not teams:
        teams = DEFAULT_LEAGUE_TEAMS.copy()
    enriched = []
    for t in teams:
        row = dict(t)
        row["owner"] = get_team_manager_display(row)
        if not row.get("logo_resolved"):
            fallback_logo = f"https://g.espncdn.com/lm-static/ffl/images/default_logos/{(int(row.get('team_id', 1)) % 20) or 1}.svg"
            row["logo_resolved"] = row.get("logo", "") or fallback_logo
        enriched.append(row)
    return enriched


def get_selected_espn_team():
    selected_team_id = st.session_state.espn_selected_team_id
    if selected_team_id is None:
        return None
    teams = get_preferred_teams()
    for team in teams:
        if team.get("team_id") == selected_team_id:
            return team
    return None


def _render_global_navigation():
    st.markdown(
        """
        <style>
        div[data-testid="stButton"]{margin-bottom:0.2rem;}
        div[data-testid="stButton"] > button{padding-top:0.35rem;padding-bottom:0.35rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    nav_cols = st.columns(7, gap="small")
    nav_buttons = [
        ("Home", "Landing", "nav_home"),
        ("Simulator", "Draft simulator", "nav_sim"),
        ("Research", "Draft research", "nav_research"),
        ("League history", "League history", "nav_league"),
        ("Profiles", "Profiles", "nav_profiles"),
        ("Team views", "Team views", "nav_teams"),
        ("Draft recap", "Draft recap", "nav_recap"),
    ]
    for i, (label, target_page, key) in enumerate(nav_buttons):
        if target_page == "Draft recap" and not st.session_state.drafted_players:
            continue
        with nav_cols[i]:
            if st.button(label, key=key, width="stretch"):
                st.session_state.app_page = target_page
                st.rerun()
    st.caption(f"Current page: {st.session_state.app_page}")
    st.divider()


# ============== SETTINGS ==============
with st.sidebar:
    st.header("Settings")

    if st.button("Connect ESPN", type="primary", use_container_width=True):
        if not st.session_state.espn_s2:
            st.session_state.espn_s2 = _get_local_secret("ESPN_S2")
        if not st.session_state.espn_swid:
            st.session_state.espn_swid = _get_local_secret("SWID")
        sync_espn_connection()

    if st.session_state.espn_connect_status:
        if st.session_state.espn_connected:
            st.success(st.session_state.espn_connect_status)
        else:
            st.warning(st.session_state.espn_connect_status)

    with st.form("espn_settings_form"):
        league_id_input = st.text_input("ESPN League ID", value=st.session_state.espn_league_id)
        espn_s2_input = st.text_input("espn_s2 cookie", value=st.session_state.espn_s2, type="password")
        espn_swid_input = st.text_input("SWID (optional)", value=st.session_state.espn_swid, type="password")
        settings_saved = st.form_submit_button("Save ESPN Settings", type="primary")

    if settings_saved:
        prior_league = st.session_state.espn_league_id
        st.session_state.espn_league_id = league_id_input.strip()
        st.session_state.espn_s2 = espn_s2_input.strip()
        st.session_state.espn_swid = espn_swid_input.strip()
        if st.session_state.espn_league_id != prior_league:
            st.session_state.espn_selected_team_id = None
            st.session_state.espn_selected_team_name = None
            st.session_state.espn_selected_owner_id = None
            st.session_state.espn_selected_owner_name = None
        sync_espn_connection()
        st.success("Settings saved and connection tested.")

_render_global_navigation()

if st.session_state.app_page == "Landing":
    _render_landing_page()
    st.divider()
    st.caption("2026 Fantasy Football Draft Simulator v3.0 | 21 Mock Drafts | 240 Players | 5 ADP Sources")
    st.stop()

if st.session_state.app_page == "Draft research":
    _render_draft_research_page()
    st.divider()
    st.caption("2026 Fantasy Football Draft Simulator v3.0 | 21 Mock Drafts | 240 Players | 5 ADP Sources")
    st.stop()

if st.session_state.app_page == "League history":
    _render_league_history_page()
    st.divider()
    st.caption("2026 Fantasy Football Draft Simulator v3.0 | 21 Mock Drafts | 240 Players | 5 ADP Sources")
    st.stop()

if st.session_state.app_page == "Profiles":
    _render_profiles_page()
    st.divider()
    st.caption("2026 Fantasy Football Draft Simulator v3.0 | 21 Mock Drafts | 240 Players | 5 ADP Sources")
    st.stop()

if st.session_state.app_page == "Team views":
    _render_team_views_hub()
    st.divider()
    st.caption("2026 Fantasy Football Draft Simulator v3.0 | 21 Mock Drafts | 240 Players | 5 ADP Sources")
    st.stop()

if st.session_state.app_page == "Draft recap":
    _render_standalone_draft_recap()
    st.divider()
    st.caption("2026 Fantasy Football Draft Simulator v3.0 | 21 Mock Drafts | 240 Players | 5 ADP Sources")
    st.stop()


# ============== DRAFT SETUP PAGE ==============
if st.button("Back to home", key="sim_back_home"):
    st.session_state.app_page = "Landing"
    st.rerun()

if not st.session_state.draft_started:
    st.title("🏈 2026 Fantasy Football Draft Simulator")
    st.subheader("Select ESPN Team & Draft Slot")

    with st.expander("ESPN League Sync", expanded=True):
        st.caption(f"League **{st.session_state.espn_league_id or 'not set'}**. Click sync to refresh teams and slots.")
        if st.button("Sync League Teams", key="sync_league_button", type="secondary"):
            sync_espn_connection()
        if not st.session_state.espn_s2:
            st.warning("No espn_s2 set. Add credentials in Settings to enable team sync.")

        espn_teams = st.session_state.espn_teams_cache if st.session_state.espn_teams_cache else DEFAULT_LEAGUE_TEAMS.copy()

        if st.session_state.espn_connect_status:
            if st.session_state.espn_connected:
                st.success(st.session_state.espn_connect_status)
            else:
                st.warning(st.session_state.espn_connect_status)

        selected_team_slot = None
        if espn_teams:
            label_to_team = {}
            team_labels = []
            for t in espn_teams:
                slot_txt = f"Slot {t['draft_slot']}" if t.get("draft_slot") else "Slot unknown"
                owner_txt = f" • {t['owner']}" if t.get("owner") else ""
                label = f"{t['name']} ({t.get('abbrev','')}) • {slot_txt}{owner_txt}"
                team_labels.append(label)
                label_to_team[label] = t

            default_label_index = 0
            if st.session_state.espn_selected_team_id is not None:
                for i, lbl in enumerate(team_labels):
                    if label_to_team[lbl]["team_id"] == st.session_state.espn_selected_team_id:
                        default_label_index = i
                        break

            selected_team_label = st.selectbox("Select your ESPN team", team_labels, index=default_label_index)
            selected_team = label_to_team[selected_team_label]
            st.session_state.espn_selected_team_id = selected_team["team_id"]
            st.session_state.espn_selected_team_name = selected_team["name"]
            st.session_state.espn_selected_owner_id = selected_team.get("owner_id")
            st.session_state.espn_selected_owner_name = selected_team.get("owner", "")
            selected_team_slot = selected_team.get("draft_slot")

            p1, p2 = st.columns([1, 3])
            with p1:
                team_logo_src = selected_team.get("logo_resolved") or selected_team.get("logo")
                if team_logo_src:
                    fallback_logo = f"https://g.espncdn.com/lm-static/ffl/images/default_logos/{(int(selected_team.get('team_id', 1)) % 20) or 1}.svg"
                    st.markdown(
                        f'<img src="{team_logo_src}" width="72" '
                        f'onerror="this.onerror=null;this.src=\'{fallback_logo}\';" '
                        f'style="border-radius:8px;border:1px solid #e2e8f0;background:#fff;">',
                        unsafe_allow_html=True
                    )
            with p2:
                st.caption(f"Selected team: {selected_team['name']} ({selected_team.get('abbrev','')})")
                if selected_team_slot:
                    st.success(f"Detected draft slot: #{selected_team_slot}")
                else:
                    st.info("Draft slot not found from ESPN draft data; select manually below.")

    slot_default = int(selected_team_slot) if selected_team_slot else int(st.session_state.draft_slot or 6)
    slot_default = max(1, min(12, slot_default))

    col1, col2 = st.columns([2, 1])
    with col1:
        slot = st.slider(
            "Choose your draft slot",
            min_value=1,
            max_value=12,
            value=slot_default,
            step=1,
            help="Pick position in your 12-team league (auto-filled from ESPN team when available)."
        )
        st.session_state.draft_slot = slot
    with col2:
        st.metric("You're Picking", f"#{slot}")
    
    st.divider()
    
    st.header("Draft Position Analysis")
    slot_strategies = df_full_strategies[df_full_strategies['Slot'] == slot].copy()
    slot_strategies = slot_strategies.sort_values(['Rank', 'Value_Score'], ascending=[True, False])
    
    st.write(f"""
    **Your Draft Position Analysis:**
    - **Round 1:** Your pick is #{slot}
    - **Round 2:** Your pick is #{13-slot} (snake back)
    - **Rounds 3-5:** Alternating picks based on league size
    """)
    
    # Strategy Selection with Dropdown
    st.header("Select Your Draft Strategy")
    st.caption("Choose from all strategies for your slot")
    
    if not slot_strategies.empty:
        # Build strategy options
        strategy_labels = []
        for _, strat in slot_strategies.iterrows():
            recommended_badge = " [RECOMMENDED]" if strat['Is_Recommended'] else ""
            strategy_labels.append(f"{strat['Strategy_Name']}{recommended_badge}")
        
        # Dropdown selector
        selected_strategy_label = st.selectbox(
            "Choose your strategy:",
            strategy_labels,
            help="Select which strategy to follow for your draft"
        )
        
        # Get the selected strategy details
        selected_idx = strategy_labels.index(selected_strategy_label)
        selected_strat = slot_strategies.iloc[selected_idx]
        selected_strategy_row = get_strategy_row(slot, selected_strat['Strategy_Name'])
        
        # Display selected strategy in detail
        st.divider()
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.subheader(f"{selected_strat['Strategy_Name']}")
            if selected_strat['Is_Recommended']:
                st.success("Recommended for your draft slot!")
        
        with col2:
            if 'Pattern' in selected_strat and pd.notna(selected_strat['Pattern']):
                st.info(f"**Strategy Pattern**\n{selected_strat['Pattern']}")
            st.write(selected_strat['Description'])
            st.caption(get_strategy_summary(selected_strategy_row))
        
        with col3:
            st.metric("Value Score", f"{selected_strat['Value_Score']:.3f}")
            if 'Avg_ADP' in selected_strat and pd.notna(selected_strat['Avg_ADP']) and selected_strat['Avg_ADP'] > 0:
                st.metric("Avg ADP", f"{selected_strat['Avg_ADP']:.1f}")
        
        # Preview selected strategy picks
        st.subheader("Strategy Preview (Rounds 1-5)")
        pick_cols = st.columns(5)
        for round_num in range(1, 6):
            with pick_cols[round_num - 1]:
                pick_name = f"Round{round_num}_Pick"
                st.write(f"**R{round_num}**")
                if pick_name in selected_strat and pd.notna(selected_strat[pick_name]):
                    st.info(str(selected_strat[pick_name]))
                else:
                    st.info("(Flexible)")
        
        st.divider()
        
        # Start draft button
        if st.button("START DRAFT WITH THIS STRATEGY", key="start_draft", type="primary", use_container_width=True):
            st.session_state.strategy = selected_strat['Strategy_Name']
            st.session_state.draft_started = True
            st.rerun()

# ============== DRAFT IN PROGRESS ==============
else:
    # Colorful banner with round + pick + strategy
    current_round_banner = st.session_state.current_round
    draft_slot_banner = st.session_state.draft_slot
    strategy_banner = st.session_state.strategy or "—"
    selected_team_banner = get_selected_espn_team()
    selected_team_name_banner = (
        f"{selected_team_banner.get('name', '')} ({selected_team_banner.get('abbrev', '')})".strip()
        if selected_team_banner
        else (st.session_state.espn_selected_team_name or "—")
    )
    current_pick_banner = get_pick_number(current_round_banner, draft_slot_banner)
    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#1e3a5f,#0ea5e9);border-radius:14px;padding:18px 24px;margin-bottom:12px;display:flex;align-items:center;gap:32px;flex-wrap:wrap;">
            <div style="text-align:center;">
                <div style="font-size:13px;color:#bae6fd;font-weight:600;letter-spacing:1px;">SLOT</div>
                <div style="font-size:36px;font-weight:900;color:#fff;">#{draft_slot_banner}</div>
            </div>
            <div style="width:2px;background:#38bdf8;height:50px;"></div>
            <div style="text-align:center;">
                <div style="font-size:13px;color:#bae6fd;font-weight:600;letter-spacing:1px;">ROUND</div>
                <div style="font-size:36px;font-weight:900;color:#fbbf24;">{current_round_banner} <span style="font-size:16px;color:#bae6fd;">of 16</span></div>
            </div>
            <div style="width:2px;background:#38bdf8;height:50px;"></div>
            <div style="text-align:center;">
                <div style="font-size:13px;color:#bae6fd;font-weight:600;letter-spacing:1px;">YOUR PICK #</div>
                <div style="font-size:36px;font-weight:900;color:#4ade80;">{current_pick_banner}</div>
            </div>
            <div style="width:2px;background:#38bdf8;height:50px;"></div>
            <div style="text-align:center;">
                <div style="font-size:13px;color:#bae6fd;font-weight:600;letter-spacing:1px;">STRATEGY</div>
                <div style="font-size:20px;font-weight:800;color:#f9a8d4;">{strategy_banner}</div>
            </div>
            <div style="width:2px;background:#38bdf8;height:50px;"></div>
            <div style="text-align:center;">
                <div style="font-size:13px;color:#bae6fd;font-weight:600;letter-spacing:1px;">TEAM</div>
                <div style="font-size:20px;font-weight:800;color:#fef08a;">{selected_team_name_banner}</div>
            </div>
        </div>""",
        unsafe_allow_html=True
    )
    backfill_drafted_avg_adp(st.session_state.drafted_players, df_players)
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Draft Board", "🔥 Sleepers", "⚠️ Traps", "📊 Analytics", "📝 Recap"])
    
    # ============== TAB 1: DRAFT BOARD ==============
    with tab1:
        current_pick = get_pick_number(st.session_state.current_round, st.session_state.draft_slot)

        drafted_names = {p['player'] for p in st.session_state.drafted_players}
        remaining_starters, remaining_flex, remaining_bench = get_roster_status(st.session_state.drafted_players)
        available, adp_upper = get_available_targets(df_players, drafted_names, current_pick, min_options=6, base_window=2)
        late_round_required = get_late_round_required_targets(
            df_players,
            drafted_names,
            remaining_starters,
            remaining_flex,
            st.session_state.current_round
        )
        if late_round_required is not None:
            available = late_round_required
            if not available.empty:
                adp_upper = float(available['ADP_Resolved'].max())
                available['May_Not_Be_There'] = False

        strategy_row = get_strategy_row(st.session_state.draft_slot, st.session_state.strategy)
         
        suggested = get_suggested_player(
            available,
            strategy_row,
            st.session_state.current_round,
            remaining_starters,
            remaining_flex,
            remaining_bench
        )

        st.subheader("Roster Needs")
        needs_parts = []
        for pos in ["QB", "RB", "WR", "TE", "DEF", "K"]:
            if remaining_starters[pos] > 0:
                needs_parts.append(f"{pos} x{remaining_starters[pos]}")
        if remaining_flex > 0:
            needs_parts.append(f"FLEX x{remaining_flex} (RB/WR/TE)")
        if remaining_bench > 0:
            needs_parts.append(f"BENCH x{remaining_bench}")
        st.info(" | ".join(needs_parts) if needs_parts else "Roster complete")
        if late_round_required is not None:
            st.info("Late-round roster completion mode: showing only open non-bench positions.")

        roster_visual = get_roster_visual(st.session_state.drafted_players)

        st.markdown("<p style='font-size:11px;font-weight:700;letter-spacing:1.2px;color:#94a3b8;text-transform:uppercase;margin-bottom:4px;'>Roster Status</p>", unsafe_allow_html=True)
        for _, row in roster_visual.iterrows():
            pos = row["Position"]
            drafted = int(row["Drafted"])
            required = int(row["Required"])
            needed = int(row["Needed"])
            pct = min(1.0, drafted / required) if required > 0 else 1.0

            if needed == 0:
                badge = "🟢 FILLED"; badge_color = "#15803d"
            elif drafted > 0:
                badge = f"🟡 {needed} LEFT"; badge_color = "#92400e"
            else:
                badge = "🔴 OPEN"; badge_color = "#991b1b"

            rc1, rc2, rc3 = st.columns([1, 4, 1.5])
            with rc1:
                st.markdown(f"<span style='font-size:12px;font-weight:700;color:#cbd5e1;'>{pos}</span>", unsafe_allow_html=True)
            with rc2:
                st.progress(pct)
            with rc3:
                st.markdown(f"<span style='font-size:11px;font-weight:700;color:{badge_color};'>{badge} &nbsp;{drafted}/{required}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:6px 0;border:none;border-top:1px solid #e2e8f0;'>", unsafe_allow_html=True)

        if suggested is not None:
            st.subheader("Suggested Pick")
            st.success(
                f"Pick #{current_pick}: {suggested['Player']} | {suggested['Position']} | {suggested['Team']} | Avg ADP {suggested['Avg_ADP_Resolved']:.1f}"
            )

        st.write(f"**{len(available)} realistic targets (ADP {current_pick:.0f} to {adp_upper:.0f})**")
        st.caption("Red player name = Avg ADP is within 1 pick before yours, so they may already be gone.")
        if available.empty:
            st.warning("No realistic targets in this strict ADP window for this pick.")
        else:
            cols_display = st.columns([0.5, 0.8, 3, 0.9, 1, 1, 1, 1, 1, 1, 1])
            with cols_display[0]:
                st.write("**#**")
            with cols_display[1]:
                st.write("")
            with cols_display[2]:
                st.write("**Player**")
            with cols_display[3]:
                st.write("**Info**")
            with cols_display[4]:
                st.write("**Pos**")
            with cols_display[5]:
                st.write("**Team**")
            with cols_display[6]:
                st.write("**Pick #**")
            with cols_display[7]:
                st.write("**Avg ADP**")
            with cols_display[8]:
                st.write("**Fit**")
            with cols_display[9]:
                st.write("**Strategy**")
            with cols_display[10]:
                st.write("**Action**")

            st.divider()

            needed_pos_set = {pos for pos in ["QB", "RB", "WR", "TE", "DEF", "K"] if remaining_starters[pos] > 0}
            if remaining_flex > 0:
                needed_pos_set.update({"RB", "WR", "TE"})

            for idx, (_, player) in enumerate(available.head(25).iterrows(), 1):
                cols = st.columns([0.5, 0.8, 3, 0.9, 1, 1, 1, 1, 1, 1, 1])
                team = str(player.get('Team', '')).strip()
                team_slug = team.lower().replace('jac', 'jax').replace('was', 'wsh')
                with cols[0]:
                    st.write(f"{idx}")
                with cols[1]:
                    headshot = player.get('Headshot_URL', '')
                    is_defense = str(player.get('Position', '')).strip().upper() == 'DEF'
                    if is_defense and team and team != 'nan':
                        st.markdown(
                            f'<img src="https://a.espncdn.com/i/teamlogos/nfl/500/{team_slug}.png" width="40" height="40" '
                            f'style="object-fit:contain;">',
                            unsafe_allow_html=True
                        )
                    elif headshot and str(headshot) != 'nan' and str(headshot).startswith('http'):
                        st.markdown(f'<img src="{headshot}" width="40" height="40" style="border-radius:50%;object-fit:cover;border:1px solid #e2e8f0;">', unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="width:40px;height:40px;border-radius:50%;background:#e2e8f0;"></div>', unsafe_allow_html=True)
                with cols[2]:
                    if bool(player.get('May_Not_Be_There', False)):
                        st.markdown(f"<span style='color:#dc2626'><b>{player['Player']}</b></span>", unsafe_allow_html=True)
                    else:
                        st.write(f"**{player['Player']}**")
                with cols[3]:
                    if st.button("INFO", key=f"info_{idx}_{player['Player']}", type="secondary"):
                        st.session_state.selected_player_info = {
                            "Player": str(player.get("Player", "")),
                            "Team": str(player.get("Team", "")),
                            "Position": str(player.get("Position", "")),
                        }
                        st.rerun()
                with cols[4]:
                    st.write(player['Position'])
                with cols[5]:
                    if team and team != 'nan':
                        st.markdown(f'<img src="https://a.espncdn.com/i/teamlogos/nfl/500/{team_slug}.png" width="28" title="{team}" style="vertical-align:middle;">', unsafe_allow_html=True)
                    else:
                        st.write("—")
                with cols[6]:
                    st.write(f"{current_pick}")
                with cols[7]:
                    st.write(f"{player['Avg_ADP_Resolved']:.1f}" if pd.notna(player['Avg_ADP_Resolved']) else "—")
                with cols[8]:
                    st.write("✅ Need" if player['Position'] in needed_pos_set else "—")
                with cols[9]:
                    st.write(get_strategy_fit_label(player, strategy_row, st.session_state.current_round))
                with cols[10]:
                    if st.button("PICK", key=f"pick_{idx}_{player['Player']}", type="primary"):
                        st.session_state.drafted_players.append({
                            'player': player['Player'],
                            'pos': player['Position'],
                            'team': player['Team'],
                            'round': st.session_state.current_round,
                            'adp': player.get('ADP_Resolved', player.get('Final_ADP', np.nan)),
                            'avg_adp': player['Avg_ADP_Resolved'],
                            'tier': player.get('Tier', np.nan),
                            'pick_number': current_pick
                        })
                        st.session_state.selected_player_info = None
                        st.session_state.current_round += 1
                        st.rerun()

            selected_info = st.session_state.get("selected_player_info")
            if selected_info:
                try:
                    sleeper_players, sleeper_proj_2026, sleeper_stats_2024 = load_sleeper_data()
                    sleeper_id, sleeper_player = find_sleeper_player(
                        sleeper_players,
                        selected_info.get("Player", ""),
                        selected_info.get("Team", ""),
                        selected_info.get("Position", ""),
                    )
                except Exception:
                    sleeper_id, sleeper_player = None, None
                    sleeper_proj_2026, sleeper_stats_2024 = {}, {}

                st.markdown("#### Player Detail")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Player", selected_info.get("Player", "—"))
                with c2:
                    st.metric("Position", selected_info.get("Position", "—"))
                with c3:
                    st.metric("Team", selected_info.get("Team", "—"))
                with c4:
                    st.metric("Sleeper ID", sleeper_id if sleeper_id else "Not found")

                if sleeper_player:
                    news_ts = sleeper_player.get("news_updated")
                    news_dt = datetime.fromtimestamp(news_ts / 1000).strftime("%Y-%m-%d %H:%M") if news_ts else "N/A"
                    st.caption(
                        f"Sleeper update: {news_dt} | Status: {sleeper_player.get('status', 'N/A')} | "
                        f"Injury: {sleeper_player.get('injury_status') or 'None'}"
                    )

                if sleeper_id:
                    proj = sleeper_proj_2026.get(str(sleeper_id), {})
                    stats = sleeper_stats_2024.get(str(sleeper_id), {})
                    try:
                        weekly_proj = load_sleeper_weekly_projections(sleeper_id, season=2026)
                    except Exception:
                        weekly_proj = {}

                    p1, p2, p3, p4 = st.columns(4)
                    with p1:
                        st.metric("2026 Proj PPR", f"{float(proj.get('pts_ppr', 0)):.1f}" if proj else "—")
                    with p2:
                        st.metric("2026 Proj GP", f"{float(proj.get('gp', 0)):.0f}" if proj else "—")
                    with p3:
                        st.metric("2024 PPR", f"{float(stats.get('pts_ppr', 0)):.1f}" if stats else "—")
                    with p4:
                        st.metric("2024 GP", f"{float(stats.get('gp', 0)):.0f}" if stats else "—")

                    week_options = sorted(
                        [str(k) for k, v in weekly_proj.items() if isinstance(v, dict) and v.get("stats")],
                        key=lambda w: int(w)
                    )
                    if week_options:
                        selected_week = st.selectbox(
                            "2026 Projection Week",
                            week_options,
                            index=len(week_options) - 1,
                            key=f"week_proj_{sleeper_id}"
                        )
                        wk = weekly_proj.get(selected_week, {})
                        wk_stats = wk.get("stats", {}) if isinstance(wk, dict) else {}
                        w1, w2, w3, w4 = st.columns(4)
                        with w1:
                            st.metric("Week PPR", f"{float(wk_stats.get('pts_ppr', 0)):.1f}" if wk_stats else "—")
                        with w2:
                            st.metric("Week Std", f"{float(wk_stats.get('pts_std', 0)):.1f}" if wk_stats else "—")
                        with w3:
                            st.metric("Week Half", f"{float(wk_stats.get('pts_half_ppr', 0)):.1f}" if wk_stats else "—")
                        with w4:
                            st.metric("Week GP", f"{float(wk_stats.get('gp', 0)):.0f}" if wk_stats else "—")
                    else:
                        st.caption("No week-by-week 2026 projection rows available yet for this player.")

                query = urllib.parse.quote_plus(f"{selected_info.get('Player', '')} {selected_info.get('Team', '')} nfl news")
                team_slug = normalize_team_abbr(selected_info.get("Team", "")).lower()
                st.markdown(
                    f"[Search Latest News](https://www.google.com/search?q={query})"
                    + (f" | [Team Page](https://www.espn.com/nfl/team/_/name/{team_slug})" if team_slug else "")
                )
    
    # ============== TAB 2: SLEEPERS ==============
    with tab2:
        st.subheader("🔥 Elite Sleepers (Undervalued)")
        
        for _, sleeper in df_sleepers.head(10).iterrows():
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**{sleeper['Player']}**")
                st.caption(f"{sleeper['Position']} | {sleeper['Team']}")
            with col2:
                st.write(f"Undervalued by +{sleeper['Undervalued_By']:.0f}")
            with col3:
                if st.button("ADD", key=f"sleeper_{sleeper['Player']}"):
                    st.session_state.drafted_players.append({
                        'player': sleeper['Player'],
                        'pos': sleeper['Position'],
                        'team': sleeper['Team'],
                        'round': st.session_state.current_round,
                        'adp': 0
                    })
                    st.rerun()
            st.divider()
    
    # ============== TAB 3: TRAPS ==============
    with tab3:
        st.subheader("⚠️ Trap Picks (Avoid)")
        
        for _, trap in df_traps.head(8).iterrows():
            col1, col2 = st.columns([2, 2])
            
            with col1:
                st.write(f"**{trap['Player']}** 🔴")
                st.caption(f"{trap['Position']} | {trap['Team']}")
            with col2:
                st.warning(f"Overvalued by -{trap['Overvalued_By']:.0f} spots")
            st.divider()
    
    # ============== TAB 4: ANALYTICS ==============
    with tab4:
        st.subheader("📊 Draft Analytics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            rbs = len([p for p in st.session_state.drafted_players if p['pos'] == 'RB'])
            st.metric("Running Backs", rbs)
        
        with col2:
            wrs = len([p for p in st.session_state.drafted_players if p['pos'] == 'WR'])
            st.metric("Wide Receivers", wrs)
        
        with col3:
            st.metric("Total Picks", len(st.session_state.drafted_players))

        if st.session_state.drafted_players:
            avg_adp_values = [p.get('avg_adp') for p in st.session_state.drafted_players if pd.notna(p.get('avg_adp'))]
            if avg_adp_values:
                st.metric("Avg ADP of Drafted", f"{np.mean(avg_adp_values):.1f}")

        roster_visual = get_roster_visual(st.session_state.drafted_players)
        st.write("#### Roster Built vs Needed")
        st.dataframe(roster_visual, use_container_width=True, hide_index=True)
        st.bar_chart(roster_visual.set_index("Position")[["Drafted", "Needed"]])
        
        st.write("#### Your Picks So Far:")
        if st.session_state.drafted_players:
            draft_df = pd.DataFrame(st.session_state.drafted_players)
            display_cols = [c for c in ['round', 'pick_number', 'player', 'pos', 'team', 'avg_adp'] if c in draft_df.columns]
            st.dataframe(draft_df[display_cols], use_container_width=True)
    
    # ============== TAB 5: RECAP ==============
    with tab5:
        if st.session_state.drafted_players:
            scores = calculate_final_scores(st.session_state.drafted_players, st.session_state.draft_slot, st.session_state.strategy)

            overall = scores["overall"]
            if overall >= 75:
                grade = "A"; grade_label = "ELITE DRAFT"; bar_color = "#16a34a"; bg = "#052e16"; sub = "You nailed it. Strong value, depth, and strategy adherence."
            elif overall >= 60:
                grade = "B"; grade_label = "SOLID DRAFT"; bar_color = "#0284c7"; bg = "#0c1a2e"; sub = "Good draft. A few opportunities left on the board."
            elif overall >= 45:
                grade = "C"; grade_label = "AVERAGE DRAFT"; bar_color = "#d97706"; bg = "#1c1008"; sub = "Serviceable, but some positional or value gaps to address."
            else:
                grade = "D"; grade_label = "NEEDS WORK"; bar_color = "#dc2626"; bg = "#1c0505"; sub = "Significant value or strategy issues. Review your picks."

            st.markdown(
                f"""<div style="background:{bg};border-radius:12px;padding:24px 32px;display:flex;align-items:center;gap:32px;margin-bottom:16px;">
                    <div style="text-align:center;min-width:80px;">
                        <div style="font-size:64px;font-weight:900;color:{bar_color};line-height:1;">{grade}</div>
                        <div style="font-size:10px;font-weight:700;letter-spacing:1.5px;color:#94a3b8;text-transform:uppercase;margin-top:4px;">Grade</div>
                    </div>
                    <div style="border-left:2px solid #1e293b;height:70px;"></div>
                    <div>
                        <div style="font-size:22px;font-weight:800;color:#f8fafc;letter-spacing:.5px;">{grade_label}</div>
                        <div style="font-size:13px;color:#94a3b8;margin-top:6px;">{sub}</div>
                        <div style="margin-top:12px;background:#1e293b;border-radius:99px;height:6px;width:220px;overflow:hidden;">
                            <div style="width:{int(overall)}%;background:{bar_color};height:6px;border-radius:99px;"></div>
                        </div>
                        <div style="font-size:11px;color:#64748b;margin-top:4px;">Overall Score: {overall:.0f} / 100</div>
                    </div>
                </div>""",
                unsafe_allow_html=True
            )

            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.metric("Tier Quality", f"{scores['tier']:.0f}")
            with s2:
                st.metric("ADP Value", f"{scores['value']:.0f}")
            with s3:
                st.metric("Strategy Fit", f"{scores['adherence']:.0f}")
            with s4:
                st.metric("Overall", f"{scores['overall']:.0f}")

            advice = []
            if scores["tier"] < 70:
                advice.append("Drafted too many low-tier players.")
            else:
                advice.append("Strong tier quality.")
            if scores["value"] < 70:
                advice.append("Too many picks were far from ideal ADP value.")
            else:
                advice.append("Good ADP value discipline.")
            if scores["adherence"] < 70:
                advice.append("You drifted from your chosen strategy too often.")
            else:
                advice.append("You followed your strategy well.")
            st.info("Advice: " + " ".join(advice))

            st.subheader("✅ Your Draft Build")
            draft_df = pd.DataFrame(st.session_state.drafted_players)
            st.dataframe(draft_df.rename(columns={
                'player': 'Player',
                'pos': 'Position',
                'team': 'Team',
                'round': 'Round',
                'avg_adp': 'Avg_ADP'
            }), use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Continue Drafting"):
                    st.rerun()
            with col2:
                if st.button("End Draft & Export"):
                    st.write("Draft complete! Ready to download.")
        else:
            st.info("Start picking to see your draft build")

st.divider()
st.caption("2026 Fantasy Football Draft Simulator v3.0 | 21 Mock Drafts | 240 Players | 5 ADP Sources")
