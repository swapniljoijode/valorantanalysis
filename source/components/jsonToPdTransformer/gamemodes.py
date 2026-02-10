import pandas as pd
from typing import List, Dict, Any

def gamemodes_json_to_df(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Transform raw /gamemodes JSON (list of dicts) into a clean DataFrame.
    """
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

    return pd.DataFrame(records)
