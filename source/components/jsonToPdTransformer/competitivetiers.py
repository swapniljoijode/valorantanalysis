import pandas as pd
from typing import List, Dict, Any

def competitivetiers_json_to_df(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Transform raw /competitivetiers JSON (list of dicts) into a clean DataFrame.
    """
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


    return pd.DataFrame(records)
       
   