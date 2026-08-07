import pandas as pd

# Load complete player database
df = pd.read_csv('data/complete_player_database.csv')

# Check if Geno Smith already exists
if 'Geno Smith' not in df['Player'].values:
    # Add Geno Smith
    new_row = {
        'Player': 'Geno Smith',
        'ADP_15rd': None,
        'ADP_Combined': None,
        'ADP_Avg_5way': None,
        'Master_ADP': 183.0,
        'ADP_Std_Dev': None,
        'Num_Sources': 1,
        'Rank': 208,
        'Position': 'QB',
        'Team': 'NYJ',
        'Final_ADP': 183.0,
        'Image_URL': '',
        'Tier': 'Late'
    }
    
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv('data/complete_player_database.csv', index=False)
    print('Added Geno Smith (QB, NYJ, ADP 183) to complete_player_database.csv')
else:
    print('Geno Smith already in database')
