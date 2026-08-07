"""Jets Focus Draft Strategy - prioritize NY Jets players in best available positions"""

import csv
import os
from typing import Dict, List, Tuple


def get_jets_players(rankings_file: str) -> List[Dict[str, str]]:
    """Extract all NY Jets players from rankings data"""
    jets_players = []
    
    if not os.path.exists(rankings_file):
        return jets_players
    
    # Load from complete_player_database.csv which has Team column
    db_path = os.path.join(os.path.dirname(__file__), "data", "complete_player_database.csv")
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Team') == 'NYJ':
                    jets_players.append({
                        'Player': row.get('Player', ''),
                        'Position': row.get('Position', ''),
                        'Master_ADP': row.get('Master_ADP', '999'),
                        'Team': 'NYJ'
                    })
    
    # Sort by ADP
    jets_players.sort(key=lambda x: float(x.get('Master_ADP', 999)))
    return jets_players


def build_jets_strategy() -> Dict[str, List[str]]:
    """Build a Jets-focused draft strategy targeting optimal positions"""
    jets_list = get_jets_players('')
    
    strategy = {
        'Early Targets': [],  # Best positioned Jets with early ADP
        'Mid Targets': [],     # Mid-tier Jets players
        'Late Options': [],    # Late round Jets value
    }
    
    for player in jets_list:
        adp = float(player['Master_ADP'])
        pos = player['Position']
        name = player['Player']
        
        if adp < 50 and pos in ['RB', 'WR']:
            strategy['Early Targets'].append(f"{name} ({pos}) - ADP: {adp}")
        elif adp < 100:
            strategy['Mid Targets'].append(f"{name} ({pos}) - ADP: {adp}")
        else:
            strategy['Late Options'].append(f"{name} ({pos}) - ADP: {adp}")
    
    return strategy


if __name__ == '__main__':
    strat = build_jets_strategy()
    print("NEW YORK JETS DRAFT STRATEGY")
    print("=" * 50)
    for tier, players in strat.items():
        print(f"\n{tier}:")
        for player in players:
            print(f"  - {player}")
