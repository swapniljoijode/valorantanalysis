from source import logging, CustomException
import sys
import pandas as pd
from source.components.matchTimeline import generate_all_match_details
from source.components.apiClient.valorant_api_client import ValorantAPIClient
from source.components.jsonToPdTransformer.agents import agents_json_to_df
from source.components.jsonToPdTransformer.weapons import weapons_json_to_df
from source.components.jsonToPdTransformer.maps import maps_json_to_df
from source.components.jsonToPdTransformer.gamemodes import gamemodes_json_to_df
from source.components.jsonToPdTransformer.gears import gears_json_to_df
from source.components.jsonToPdTransformer.competitivetiers import competitivetiers_json_to_df
from source.components.users import synthetic_users
from source.components.warehouse.postgres_loader import load_all


def build_dimension_data():
    """Fetch raw JSON from the Valorant API, transform to DataFrames, save CSVs."""
    client = ValorantAPIClient()

    # 1) Fetch raw JSON from API
    agents_json = client.get_agents()
    weapons_json = client.get_weapons()
    maps_json = client.get_maps()
    gamemodes_json = client.get_gamemodes()
    gears_json = client.get_gears()
    competitive_tiers_json = client.get_competitive_tiers()

    # 2) Transform JSON -> DataFrame using the respective transformer
    df_agents = agents_json_to_df(agents_json)
    df_weapons = weapons_json_to_df(weapons_json)
    df_maps = maps_json_to_df(maps_json)
    df_gamemodes = gamemodes_json_to_df(gamemodes_json)
    df_gears = gears_json_to_df(gears_json)
    df_competitive_tiers = competitivetiers_json_to_df(competitive_tiers_json)
    df_users = synthetic_users(df_competitive_tiers)

    # 3) Save dimension CSVs (landing zone)
    df_agents.to_csv("data/agents_dim.csv", index=False)
    df_weapons.to_csv("data/weapons_dim.csv", index=False)
    df_maps.to_csv("data/maps_dim.csv", index=False)
    df_gamemodes.to_csv("data/gamemodes_dim.csv", index=False)
    df_gears.to_csv("data/gears_dim.csv", index=False)
    df_competitive_tiers.to_csv("data/competitive_tiers_dim.csv", index=False)
    df_users.to_csv("data/users_dim.csv", index=False)

    return {
        "agents_dim": df_agents,
        "weapons_dim": df_weapons,
        "maps_dim": df_maps,
        "gamemodes_dim": df_gamemodes,
        "gears_dim": df_gears,
        "competitive_tiers_dim": df_competitive_tiers,
        "users_dim": df_users,
    }


def build_fact_data():
    """Generate match timeline / rank progression fact tables and save CSVs."""
    logging.info("Loading input CSV files...")
    users_df = pd.read_csv("data/users_dim.csv", parse_dates=["join_date"])
    agents_df = pd.read_csv("data/agents_dim.csv")
    maps_df = pd.read_csv("data/maps_dim.csv")
    weapons_df = pd.read_csv("data/weapons_dim.csv")
    gears_df = pd.read_csv("data/gears_dim.csv")
    logging.info(
        f"Successfully loaded input files - users: {users_df.shape}, "
        f"agents: {agents_df.shape}, maps: {maps_df.shape}"
    )

    competitive_tiers_all = pd.read_csv("data/competitive_tiers_dim.csv")["Rank"].tolist()
    remove = {"Unused1", "Unused2"}
    competitive_tiers = [x for x in competitive_tiers_all if x not in remove]

    logging.info("Generating match timeline...")
    match_status, round_status, agent_perf_status, round_spike_status, match_df, match_summary, rank_history, weapon_economy = generate_all_match_details(
        users_df,
        agents_df,
        maps_df,
        competitive_tiers,
        weapons_df,
        gears_df,
    )

    logging.info("Writing output CSV files...")
    match_status.to_csv("data/match_status.csv", index=False)
    round_status.to_csv("data/round_status.csv", index=False)
    agent_perf_status.to_csv("data/agent_perf_status.csv", index=False)
    round_spike_status.to_csv("data/round_spike_status.csv", index=False)
    match_summary.to_csv("data/match_summary.csv", index=False)
    match_df.to_csv("data/match_df.csv", index=False)
    rank_history.to_csv("data/rank_history.csv", index=False)
    weapon_economy.to_csv("data/weapon_economy.csv", index=False)
    logging.info("Saved all fact CSVs to data/")

    return {
        "match_status": match_status,
        "round_status": round_status,
        "agent_perf_status": agent_perf_status,
        "round_spike_status": round_spike_status,
        "match_summary": match_summary,
        "match_df": match_df,
        "rank_history": rank_history,
        "weapon_economy": weapon_economy,
    }


def main():
    try:
        logging.info("=" * 80)
        logging.info("Starting Valorant Data Pipeline")
        logging.info("=" * 80)

        dimensions = build_dimension_data()

        print("Agents:")
        print(dimensions["agents_dim"].head())
        print("\nWeapons:")
        print(dimensions["weapons_dim"].head())

        facts = build_fact_data()

        logging.info("Loading all tables into the PostgreSQL warehouse (raw schema)...")
        load_all({**dimensions, **facts})

        logging.info("=" * 80)
        logging.info("Pipeline Completed Successfully!")
        logging.info("=" * 80)

    except CustomException as e:
        logging.error(f"CustomException occurred: {str(e)}")
        logging.error("=" * 80)
        raise
    except Exception as e:
        error_msg = f"Unexpected error in main execution: {str(e)}"
        logging.error(error_msg)
        logging.error("=" * 80)
        raise


if __name__ == "__main__":
    main()
