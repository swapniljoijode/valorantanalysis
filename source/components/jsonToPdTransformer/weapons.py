import pandas as pd
from typing import List, Dict, Any

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

    return pd.DataFrame(records)
