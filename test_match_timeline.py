import pandas as pd
import sys
sys.path.insert(0, 'c:/Users/gjric/Desktop/ValorantAnalysis')

from source.components.matchTimeline import generate_all_match_details

# Load data
users_df = pd.read_csv("data/users_dim.csv", parse_dates=["join_date"])
agents_df = pd.read_csv("data/agents_dim.csv")
maps_df = pd.read_csv("data/maps_dim.csv")

# Test with just 1 match per day for 2 days
print("Starting test...")
try:
    match_status, round_status, agent_perf_status, round_spike_status, match_df = generate_all_match_details(
        users_df,
        agents_df,
        maps_df,
        per_day_match_counter=1,
        start_date="2025-01-01",
        end_date="2025-01-02"
    )
    print("✓ Success! No InvalidIndexError")
    print(f"Match status shape: {match_status.shape}")
    print(f"Agent performance shape: {agent_perf_status.shape}")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
