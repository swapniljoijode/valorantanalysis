from source.components.apiClient.valorant_api_client import ValorantAPIClient
from source.components.jsonToPdTransformer.agents import agents_json_to_df
from source.components.jsonToPdTransformer.weapons import weapons_json_to_df
from source.components.jsonToPdTransformer.maps import maps_json_to_df
from source.components.jsonToPdTransformer.gamemodes import gamemodes_json_to_df
from source.components.jsonToPdTransformer.gears import gears_json_to_df
from source.components.jsonToPdTransformer.competitivetiers import competitivetiers_json_to_df
from source.components.users import synthetic_users
#from src.components.matchTimeline import base_params
# from transformers.maps_transformer import maps_json_to_df
# ...

def main():
    client = ValorantAPIClient()

    # 1) Fetch raw JSON from API
    agents_json = client.get_agents()
    weapons_json = client.get_weapons()
    maps_json = client.get_maps()
    gamemodes_json = client.get_gamemodes()
    gears_json = client.get_gears()
    competitive_tiers_json = client.get_competitive_tiers()

    # 2) Transform JSON → DataFrame using the respective transformer
    df_agents = agents_json_to_df(agents_json)
    df_weapons = weapons_json_to_df(weapons_json)
    df_maps = maps_json_to_df(maps_json)
    df_gamemodes = gamemodes_json_to_df(gamemodes_json)
    df_gears = gears_json_to_df(gears_json)
    df_competitive_tiers = competitivetiers_json_to_df(competitive_tiers_json)
    df_users = synthetic_users(df_competitive_tiers)


    #df_timeline = base_params(df_users, df_agents, df_maps)


    # 3) Use/inspect/save
    print("Agents:")
    print(df_agents.head())

    print("\nWeapons:")
    print(df_weapons.head())

    # Optionally save
    df_agents.to_csv("data/agents_dim.csv", index=False)
    df_weapons.to_csv("data/weapons_dim.csv", index=False)
    df_maps.to_csv("data/maps_dim.csv", index=False)
    df_gamemodes.to_csv("data/gamemodes_dim.csv", index=False)
    df_gears.to_csv("data/gears_dim.csv", index=False)
    df_competitive_tiers.to_csv("data/competitive_tiers_dim.csv", index=False)
    df_users.to_csv("data/users_dim.csv", index=False)


if __name__ == "__main__":
    main()
