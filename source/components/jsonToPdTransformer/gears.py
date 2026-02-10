import pandas as pd
from typing import List, Dict, Any

def gears_json_to_df(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Transform raw /gears JSON (list of dicts) into a clean DataFrame.
    """
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

    return pd.DataFrame(records)
