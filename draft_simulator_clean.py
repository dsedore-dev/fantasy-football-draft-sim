import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="2026 Fantasy Draft Pro", page_icon="🏈", layout="wide")

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
    return df_players, df_availability, df_sleepers, df_traps, df_strategies, df_full_strategies, df_recommended

df_players, df_availability, df_sleepers, df_traps, df_strategies, df_full_strategies, df_recommended_strategies = load_data()

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

    if expected_pos and expected_pos in candidates["Position"].unique():
        expected_pool = candidates[candidates["Position"] == expected_pos]
        if not expected_pool.empty:
            return expected_pool.sort_values("Final_ADP").iloc[0]

    return candidates.sort_values("Final_ADP").iloc[0]


def get_available_targets(players_df, drafted_names, current_pick, min_options=6, base_window=2):
    pool = players_df[~players_df['Player'].isin(drafted_names)].copy()
    pool = pool[pool['Position'].isin(['QB', 'RB', 'WR', 'TE', 'DEF', 'K'])].copy()
    pool['Final_ADP'] = pd.to_numeric(pool['Final_ADP'], errors='coerce')
    pool['ADP_Avg_5way'] = pd.to_numeric(pool['ADP_Avg_5way'], errors='coerce')
    pool['ADP_15rd'] = pd.to_numeric(pool['ADP_15rd'], errors='coerce')
    pool['ADP_Combined'] = pd.to_numeric(pool['ADP_Combined'], errors='coerce')
    pool['Master_ADP'] = pd.to_numeric(pool['Master_ADP'], errors='coerce')
    pool = pool.dropna(subset=['Final_ADP'])

    # Ensure every player has an Avg ADP by falling back to the mean of available ADP sources.
    fallback_cols = ['ADP_Avg_5way', 'ADP_15rd', 'ADP_Combined', 'Master_ADP']
    pool['Avg_ADP_Resolved'] = pool[fallback_cols].mean(axis=1, skipna=True)
    pool['Avg_ADP_Resolved'] = pool['Avg_ADP_Resolved'].fillna(pool['Final_ADP'])

    upper_bound = current_pick + base_window
    available = pool[(pool['Final_ADP'] >= current_pick) & (pool['Final_ADP'] <= upper_bound)].copy()

    while len(available) < min_options and upper_bound < current_pick + 30:
        upper_bound += 2
        available = pool[(pool['Final_ADP'] >= current_pick) & (pool['Final_ADP'] <= upper_bound)].copy()

    available = available.sort_values('Final_ADP')
    return available, upper_bound


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
    tier_score = (tier_points / max(tier_count, 1)) if tier_count > 0 else 0.0

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
        if pd.notna(p.get('avg_adp')):
            continue
        name = p.get('player')
        if not name or name not in lookup.index:
            if pd.notna(p.get('adp')):
                p['avg_adp'] = float(p.get('adp'))
            continue
        row = lookup.loc[name]
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


# ============== DRAFT SETUP PAGE ==============
if not st.session_state.draft_started:
    st.title("🏈 2026 Fantasy Football Draft Simulator")
    st.subheader("Select Your Draft Slot")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        slot = st.slider(
            "Choose your draft slot",
            min_value=1,
            max_value=12,
            value=6,
            step=1,
            help="Select which position you're drafting from in the 12-team league"
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
    st.title("🏈 Live Draft - Slot #" + str(st.session_state.draft_slot))
    backfill_drafted_avg_adp(st.session_state.drafted_players, df_players)
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Draft Board", "🔥 Sleepers", "⚠️ Traps", "📊 Analytics", "📝 Recap"])
    
    # ============== TAB 1: DRAFT BOARD ==============
    with tab1:
        col_info, col_round = st.columns([3, 1])
        
        with col_info:
            st.subheader("Available Players (By ADP)")
        with col_round:
            st.metric("Round", st.session_state.current_round)

        current_pick = get_pick_number(st.session_state.current_round, st.session_state.draft_slot)
        st.metric("Your Pick #", current_pick)

        drafted_names = {p['player'] for p in st.session_state.drafted_players}
        available, adp_upper = get_available_targets(df_players, drafted_names, current_pick, min_options=6, base_window=2)

        remaining_starters, remaining_flex, remaining_bench = get_roster_status(st.session_state.drafted_players)
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

        if suggested is not None:
            st.subheader("Suggested Pick")
            st.success(
                f"Pick #{current_pick}: {suggested['Player']} | {suggested['Position']} | {suggested['Team']} | Avg ADP {suggested['Avg_ADP_Resolved']:.1f}"
            )

        st.write(f"**{len(available)} realistic targets (ADP {current_pick:.0f} to {adp_upper:.0f})**")
        if available.empty:
            st.warning("No realistic targets in this strict ADP window for this pick.")
        else:
            cols_display = st.columns([1, 3, 1, 1, 1, 1, 1, 1, 1])
            with cols_display[0]:
                st.write("**#**")
            with cols_display[1]:
                st.write("**Player**")
            with cols_display[2]:
                st.write("**Pos**")
            with cols_display[3]:
                st.write("**Team**")
            with cols_display[4]:
                st.write("**Pick #**")
            with cols_display[5]:
                st.write("**Avg ADP**")
            with cols_display[6]:
                st.write("**Fit**")
            with cols_display[7]:
                st.write("**Strategy**")
            with cols_display[8]:
                st.write("**Action**")

            st.divider()

            needed_pos_set = {pos for pos in ["QB", "RB", "WR", "TE", "DEF", "K"] if remaining_starters[pos] > 0}
            if remaining_flex > 0:
                needed_pos_set.update({"RB", "WR", "TE"})

            for idx, (_, player) in enumerate(available.head(25).iterrows(), 1):
                cols = st.columns([1, 3, 1, 1, 1, 1, 1, 1, 1])
                with cols[0]:
                    st.write(f"{idx}")
                with cols[1]:
                    st.write(f"**{player['Player']}**")
                with cols[2]:
                    st.write(player['Position'])
                with cols[3]:
                    st.write(player['Team'])
                with cols[4]:
                    st.write(f"{current_pick}")
                with cols[5]:
                    st.write(f"{player['Avg_ADP_Resolved']:.1f}" if pd.notna(player['Avg_ADP_Resolved']) else "—")
                with cols[6]:
                    st.write("✅ Need" if player['Position'] in needed_pos_set else "—")
                with cols[7]:
                    strategy_fit = "—"
                    if strategy_row is not None:
                        expected_col = f"Round{st.session_state.current_round}_Pos"
                        if expected_col in strategy_row.index and pd.notna(strategy_row[expected_col]):
                            expected_pos = str(strategy_row[expected_col]).upper()
                            strategy_fit = "✅" if str(player['Position']).upper() == expected_pos else "❌"
                    st.write(strategy_fit)
                with cols[8]:
                    if st.button("PICK", key=f"pick_{idx}_{player['Player']}"):
                        st.session_state.drafted_players.append({
                            'player': player['Player'],
                            'pos': player['Position'],
                            'team': player['Team'],
                            'round': st.session_state.current_round,
                            'adp': player['Final_ADP'],
                            'avg_adp': player['Avg_ADP_Resolved'],
                            'tier': player.get('Tier', np.nan),
                            'pick_number': current_pick
                        })
                        st.session_state.current_round += 1
                        st.rerun()
    
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

            st.subheader("🏁 Draft Result")
            if scores["overall"] >= 75:
                result_label = "GOOD DRAFT 👍"
                result_color = "#14532d"
                result_bg = "#dcfce7"
            elif scores["overall"] < 50:
                result_label = "BAD DRAFT 👎"
                result_color = "#7f1d1d"
                result_bg = "#fee2e2"
            else:
                result_label = "MIXED RESULT 👀"
                result_color = "#78350f"
                result_bg = "#fef3c7"

            st.markdown(
                f"""
                <div style="padding:16px 20px;border-radius:12px;background:{result_bg};border:2px solid {result_color};text-align:center;">
                  <div style="font-size:34px;font-weight:800;color:{result_color};letter-spacing:0.5px;">{result_label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.subheader("Draft Score")
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.metric("Tier", f"{scores['tier']:.1f}")
            with s2:
                st.metric("Value", f"{scores['value']:.1f}")
            with s3:
                st.metric("Strategy", f"{scores['adherence']:.1f}")
            with s4:
                st.metric("Overall", f"{scores['overall']:.1f}")

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
