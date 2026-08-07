import pandas as pd

# Load the full strategies file
df = pd.read_csv('data/all_strategies_16_rounds_full_roster.csv')

# Remove old Jets-Focus rows
df = df[df['Strategy_Name'] != 'Jets-Focus'].reset_index(drop=True)

# Get unique slots and max ranks
slots = sorted(df['Slot'].unique())
max_rank = df.groupby('Slot')['Rank'].max()

# Add improved Jets Focus strategy for each slot with specific Jets players
new_rows = []
for slot in slots:
    new_rank = int(max_rank[slot]) + 1
    
    # Build out picks with Jets players where applicable
    r1_pick = '(Flexible)'
    r1_pos = ''
    r2_pick = 'Breece Hall' if slot <= 8 else '(Flexible)'
    r2_pos = 'RB' if slot <= 8 else ''
    r3_pick = 'Garrett Wilson' if slot <= 10 else '(Flexible)'
    r3_pos = 'WR' if slot <= 10 else ''
    
    new_rows.append({
        'Slot': slot,
        'Rank': new_rank,
        'Strategy_Name': 'Jets-Focus',
        'Description': 'Prioritize NY Jets players (Breece Hall RB, Garrett Wilson WR)',
        'Value_Score': 0.72,
        'Strategy_Type': 'Jets-Focused',
        'Round1_Pick': r1_pick,
        'Round1_Pos': r1_pos,
        'Round2_Pick': r2_pick,
        'Round2_Pos': r2_pos,
        'Round3_Pick': r3_pick,
        'Round3_Pos': r3_pos,
        'Round4_Pick': 'RB',
        'Round4_Pos': 'RB',
        'Round5_Pick': 'WR',
        'Round5_Pos': 'WR',
        'Round6_Pick': 'No player available',
        'Round6_Pos': '',
        'Round7_Pick': 'No player available',
        'Round7_Pos': '',
        'Round8_Pick': 'No player available',
        'Round8_Pos': '',
        'Round9_Pick': 'No player available',
        'Round9_Pos': '',
        'Round10_Pick': 'No player available',
        'Round10_Pos': '',
        'Round11_Pick': 'No player available',
        'Round11_Pos': '',
        'Round12_Pick': 'No player available',
        'Round12_Pos': '',
        'Round13_Pick': 'No player available',
        'Round13_Pos': '',
        'Round14_Pick': 'No player available',
        'Round14_Pos': '',
        'Round15_Pick': 'No player available',
        'Round15_Pos': '',
        'Round16_Pick': 'No player available',
        'Round16_Pos': '',
        'Is_Recommended': False
    })

new_df = pd.DataFrame(new_rows)
df_combined = pd.concat([df, new_df], ignore_index=True)
df_combined.to_csv('data/all_strategies_16_rounds_full_roster.csv', index=False)
print(f"Updated {len(new_rows)} Jets-Focus strategies with specific positions")
