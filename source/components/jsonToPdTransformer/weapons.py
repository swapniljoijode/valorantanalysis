import pandas as pd
from typing import List, Dict, Any

# Authoritative buy-menu economy per weapon. The Valorant API's shopData is the
# primary source, but it can be null (e.g. Melee, non-standard weapons like Bandit)
# or use plural/enum category labels. The downstream economy engine
# (matchTimeline.build_weapon_pools) keys off the singular categories
# {Sidearm, SMG, Shotgun, Rifle, Sniper, Heavy, Melee} and a numeric cost, and
# drops any weapon with a null cost/category. To keep `python main.py` fully
# reproducible we normalise both fields against this canonical spec.
WEAPON_ECONOMY_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "Classic":  {"category": "Sidearm", "cost": 0},
    "Shorty":   {"category": "Sidearm", "cost": 300},
    "Frenzy":   {"category": "Sidearm", "cost": 450},
    "Ghost":    {"category": "Sidearm", "cost": 500},
    "Sheriff":  {"category": "Sidearm", "cost": 800},
    "Bandit":   {"category": "Sidearm", "cost": 600},   # non-standard weapon; user-specified
    "Stinger":  {"category": "SMG",     "cost": 1100},
    "Spectre":  {"category": "SMG",     "cost": 1600},
    "Bucky":    {"category": "Shotgun", "cost": 850},
    "Judge":    {"category": "Shotgun", "cost": 1850},
    "Bulldog":  {"category": "Rifle",   "cost": 2050},
    "Guardian": {"category": "Rifle",   "cost": 2250},
    "Phantom":  {"category": "Rifle",   "cost": 2900},
    "Vandal":   {"category": "Rifle",   "cost": 2900},
    "Marshal":  {"category": "Sniper",  "cost": 950},
    "Outlaw":   {"category": "Sniper",  "cost": 2400},
    "Operator": {"category": "Sniper",  "cost": 4700},
    "Ares":     {"category": "Heavy",   "cost": 1550},
    "Odin":     {"category": "Heavy",   "cost": 3250},
    "Melee":    {"category": "Melee",   "cost": 0},
}


def weapons_json_to_df(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Transform raw /weapons JSON (list of dicts) into a clean DataFrame.
    """
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
        # Shop economy: cost + buy-menu category. shopData is null for Melee.
        shop_data = weapon.get("shopData") or {}
        cost = shop_data.get("cost")
        category = shop_data.get("category") or shop_data.get("categoryText")
        if category is None:
            # Fall back to the top-level equippable category, stripping the enum prefix.
            raw_cat = weapon.get("category")
            category = raw_cat.split("::")[-1] if raw_cat else None
        # Normalise category/cost to the canonical economy spec (see map above) so the
        # downstream engine always sees singular categories and a numeric cost.
        override = WEAPON_ECONOMY_OVERRIDES.get(name)
        if override is not None:
            category = override["category"]
            cost = override["cost"]
        records.append({
            "uuid": uuid,
            "name": name,
            "category": category,
            "cost": cost,
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

    return pd.DataFrame(records)
