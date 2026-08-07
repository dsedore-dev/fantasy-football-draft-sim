import pandas as pd

# Check onedrive file
df = pd.read_csv('data/onedrive_mock_drafts_parsed.csv')
print('onedrive_mock_drafts_parsed.csv:')
print(f'Total rows: {len(df)}')
print(f'Columns: {list(df.columns)}')
print()

# Search for Jets players
if 'Team' in df.columns:
    jets = df[df['Team'] == 'NYJ']
    print(f'Jets players found: {len(jets)}')
    if len(jets) > 0:
        print(jets[['Player', 'Position', 'Team']].drop_duplicates().to_string())
elif 'team' in df.columns:
    jets = df[df['team'] == 'NYJ']
    print(f'Jets players found: {len(jets)}')
    if len(jets) > 0:
        print(jets.drop_duplicates().to_string())
else:
    print('No Team column - showing first row:')
    print(df.iloc[0])
    print()
    print('Checking for Jets anywhere:')
    jets_rows = df[df.astype(str).apply(lambda x: x.str.contains('NYJ|Jets', case=False).any(), axis=1)]
    print(f'Rows containing NYJ or Jets: {len(jets_rows)}')
    if len(jets_rows) > 0:
        print(jets_rows.head(10))
