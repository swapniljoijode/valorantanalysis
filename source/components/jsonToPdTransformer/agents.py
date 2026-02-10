import pandas as pd
from typing import List, Dict, Any

def agents_json_to_df(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Transform raw /agents JSON (list of dicts) into a clean DataFrame.
    """
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

    return pd.DataFrame(records)
