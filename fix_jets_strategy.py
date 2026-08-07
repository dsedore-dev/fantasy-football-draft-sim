import pandas as pd

# Load the full strategies file
df = pd.read_csv('data/all_strategies_16_rounds_full_roster.csv')

# Remove old Jets-Focus rows
df = df[df['Strategy_Name'] != 'Jets-Focus'].reset_index(drop=True)

# Get unique slots and max ranks
slots = sorted(df['Slot'].unique())
max_rank = df.groupby('Slot')['Rank'].max()

# Add improved Jets Focus strategy with all 5 Jets players
new_rows = []
for slot in slots:
    new_rank = int(max_rank[slot]) + 1
    
    new_rows.append({
        'Slot': slot,
        'Rank': new_rank,
        'Strategy_Name': 'Jets-Focus',
        'Description': 'Prioritize all NY Jets players - Breece Hall, Garrett Wilson, Omar Cooper Jr, Adonai Mitchell, Braelon Allen, Geno Smith',
        'Value_Score': 0.72,
        'Strategy_Type': 'Jets-Focused',
        'Round1_Pick': 'No player available',
        'Round1_Pos': '',
        'Round2_Pick': 'Breece Hall' if slot <= 8 else 'No player available',
        'Round2_Pos': 'RB' if slot <= 8 else '',
        'Round3_Pick': 'Garrett Wilson' if slot <= 10 else 'No player available',
        'Round3_Pos': 'WR' if slot <= 10 else '',
        'Round4_Pick': 'Braelon Allen',
        'Round4_Pos': 'RB',
        'Round5_Pick': 'Omar Cooper Jr.',
        'Round5_Pos': 'WR',
        'Round6_Pick': 'Adonai Mitchell',
        'Round6_Pos': 'WR',
        'Round7_Pick': 'Geno Smith',
        'Round7_Pos': 'QB',
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
print(f"Updated {len(new_rows)} Jets-Focus strategies with all 5 Jets players + DEF")
