import requests
import pandas as pd

# 1. Define the endpoint
URL = "https://valorant-api.com/v1/agents"

# 2. Send GET request
response = requests.get(URL, timeout=15)
response.raise_for_status()  # raise error if status != 200

# 3. Parse JSON and extract the 'data' list
data = response.json()["data"]

# 4. Normalize into a DataFrame
#    Pick a few useful fields to keep it readable
records = []
for agent in data:
    records.append({
        "uuid": agent.get("uuid"),
        "name": agent.get("displayName"),
        "role": agent.get("role", {}).get("displayName"),
        "isPlayable": agent.get("isPlayableCharacter"),
        "abilitiesCount": len(agent.get("abilities", {})),
        "ability1":agent.get("abilities", [{}])[0].get("displayName") if agent.get("abilities") else None,
        "ability2": agent.get("abilities", [{}])[1].get("displayName") if agent.get("abilities") else None,
        "ability3": agent.get("abilities", [{}])[2].get("displayName") if agent.get("abilities") else None,
        "Ultimate": agent.get("abilities", [{}])[3].get("displayName") if agent.get("abilities") else None

    })

df_agents = pd.DataFrame(records)

# 5. Print first 5 rows
print(df_agents.head(5))


"""# 1. Define the endpoint
URL = "https://valorant-api.com/v1/maps"

# 2. Send GET request
response = requests.get(URL, timeout=15)
response.raise_for_status()  # raise error if status != 200

# 3. Parse JSON and extract the 'data' list
data = response.json()["data"]

# 4. Normalize into a DataFrame
#    Pick a few useful fields to keep it readable
records = []
for map in data:
    records.append({
        "uuid": map.get("uuid"),
        "name": map.get("displayName"),
        "Icon": map.get("displayIcon")


    })

df_maps = pd.DataFrame(records)

# 5. Print first 5 rows
print(df_maps.head(5))"""


"""# 1. Define the endpoint
URL = "https://valorant-api.com/v1/competitivetiers"

# 2. Send GET request
response = requests.get(URL, timeout=15)
response.raise_for_status()  # raise error if status != 200

# 3. Parse JSON and extract the 'data' list
data = response.json()["data"]

# 4. Normalize into a DataFrame
#    Pick a few useful fields to keep it readable
records = []
for tier in data[-1:]:
    uuid = tier.get("uuid")
    episode = tier.get("assetObjectName")
    for rank in tier.get("tiers", [{}]):
        records.append({
            "uuid": uuid,
            "Episode": episode,
            "Rank": rank.get("tierName"),
            "Icon":rank.get("largeIcon")


        })

df_ranks = pd.DataFrame(records)

# 5. Print first 5 rows
print(df_ranks.head(5))"""


"""# 1. Define the endpoint
URL = "https://valorant-api.com/v1/gamemodes"

# 2. Send GET request
response = requests.get(URL, timeout=15)
response.raise_for_status()  # raise error if status != 200

# 3. Parse JSON and extract the 'data' list
data = response.json()["data"]

# 4. Normalize into a DataFrame
#    Pick a few useful fields to keep it readable
records = []
for mode in data:
    if mode.get("displayName") != "Standard":
        continue
    records.append({
        "uuid": mode.get("uuid"),
        "name": mode.get("displayName"),
        "description": mode.get("description"),
        "duration": mode.get("duration")
    

    })
    break

df_mode = pd.DataFrame(records)

# 5. Print first 5 rows
print(df_mode.head(5))"""


"""# 1. Define the endpoint
URL = "https://valorant-api.com/v1/gear"

# 2. Send GET request
response = requests.get(URL, timeout=15)
response.raise_for_status()  # raise error if status != 200

# 3. Parse JSON and extract the 'data' list
data = response.json()["data"]

# 4. Normalize into a DataFrame
#    Pick a few useful fields to keep it readable
records = []
for gears in data:

    damageReduction,damageAbsorbtion,*extras = [i.get("value") for i in gears.get("details",[{}])]
    regenPool = extras[0] if extras else None
    records.append({
        "uuid": gears.get("uuid"),
        "name": gears.get("displayName"),
        "description": gears.get("description"),
        "cost": gears.get("shopData",[{}]).get("cost"),
        "armorImage":gears.get("displayIcon"),
        "damageReduction":damageReduction,
        "damageAbsorbtion":damageAbsorbtion,
        "regenPool":regenPool

    })
    

df_gear = pd.DataFrame(records)

# 5. Print first 5 rows
print(df_gear.head(5))"""

"""# 1. Define the endpoint
URL = "https://valorant-api.com/v1/weapons"

# 2. Send GET request
response = requests.get(URL, timeout=15)
response.raise_for_status()  # raise error if status != 200

# 3. Parse JSON and extract the 'data' list
data = response.json()["data"]

# 4. Normalize into a DataFrame
#    Pick a few useful fields to keep it readable
records = []
for weapon in data:
    uuid = weapon.get("uuid")
    name = weapon.get("displayName")
    fireRate = weapon.get("weaponStats", {}).get("fireRate") if weapon.get("weaponStats") else None
    magazineSize = weapon.get("weaponStats", {}).get("magazineSize") if weapon.get("weaponStats") else None
    runSpeedMultiplier = weapon.get("weaponStats", {}).get("runSpeedMultiplier") if weapon.get("weaponStats") else None
    equipTimeSeconds = weapon.get("weaponStats", {}).get("equipTimeSeconds") if weapon.get("weaponStats") else None
    reloadTimeSeconds = weapon.get("weaponStats", {}).get("reloadTimeSeconds") if weapon.get("weaponStats") else None
    firstBulletAccuracy = weapon.get("weaponStats", {}).get("firstBulletAccuracy") if weapon.get("weaponStats") else None
    fireMode = weapon.get("weaponStats", {}).get("fireMode") if weapon.get("weaponStats") else None
    adszoomMultiplier = weapon.get("weaponStats", {}).get("adsStats", {}).get("zoomMultiplier") if weapon.get("weaponStats") and weapon.get("weaponStats", {}).get("adsStats")  else None
    adsfireRate = weapon.get("weaponStats", {}).get("adsStats", {}).get("fireRate") if weapon.get("weaponStats") and weapon.get("weaponStats", {}).get("adsStats")  else None
    adsrunSpeedMultiplier = weapon.get("weaponStats", {}).get("adsStats", {}).get("runSpeedMultiplier") if weapon.get("weaponStats") and weapon.get("weaponStats", {}).get("adsStats")  else None
    adsFirstBulletAccuracy = weapon.get("weaponStats", {}).get("adsStats", {}).get("firstBulletAccuracy") if weapon.get("weaponStats") and weapon.get("weaponStats", {}).get("adsStats")  else None
    adsburstCount = weapon.get("weaponStats", {}).get("adsStats", {}).get("burstCount") if weapon.get("weaponStats") and weapon.get("weaponStats", {}).get("adsStats")  else None
    damageRange = [{str(i.get("rangeStartMeters"))+"-"+str(i.get("rangeEndMeters")): ",".join([str(i.get("headDamage")),str(i.get("bodyDamage")),str(i.get("legDamage"))])} for i in weapon.get("weaponStats", {}).get("damageRanges", [{}])] if weapon.get("weaponStats") and weapon.get("weaponStats", {}).get("damageRanges")  else None
    range1,*extras = damageRange if damageRange else (None, )
    range2 = extras[0] if extras else None
    range3 = extras[1] if len(extras) > 1 else None
    displayIcon  = weapon.get("displayIcon")
    records.append({
        "uuid": uuid,
        "name": name,
        "fireRate": fireRate,
        "magazineSize": magazineSize,
        "runSpeedMultiplier": runSpeedMultiplier,
        "equipTimeSeconds": equipTimeSeconds,
        "reloadTimeSeconds": reloadTimeSeconds,
        "firstBulletAccuracy": firstBulletAccuracy,
        "fireMode": fireMode,
        "adszoomMultiplier": adszoomMultiplier,
        "adsfireRate": adsfireRate,
        "adsrunSpeedMultiplier": adsrunSpeedMultiplier,
        "adsFirstBulletAccuracy": adsFirstBulletAccuracy,
        "adsburstCount": adsburstCount,
        f"{",".join([i[0] for i in range1.items()]) if range1 else 'Close Range'}": ",".join([str(i[1]) for i in range1.items()]) if range1 else None,
        f"{",".join([i[0] for i in range2.items()]) if range2 else 'Mid Range'}": ",".join([str(i[1]) for i in range2.items()]) if range2 else None,
        f"{",".join([i[0] for i in range3.items()]) if range3 else 'Long Range'}": ",".join([str(i[1]) for i in range3.items()]) if range3 else None,
        "displayIcon": displayIcon

    })
    

df_weapons = pd.DataFrame(records)
df_weapons.to_csv("weapons_data.csv", index=False)
# 5. Print first 5 rows
print(df_weapons.head(5))"""