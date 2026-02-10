import pandas as pd
from typing import List, Dict, Any

def maps_json_to_df(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Transform raw /maps JSON (list of dicts) into a clean DataFrame.
    """
    records = []
    for map in data:
        records.append({
            "uuid": map.get("uuid"),
            "name": map.get("displayName"),
            "Icon": map.get("displayIcon")


        })

    return pd.DataFrame(records)
