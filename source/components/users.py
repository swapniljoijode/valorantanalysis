import pandas as pd
import numpy as np
from source.components.jsonToPdTransformer.competitivetiers import competitivetiers_json_to_df
from typing import List, Dict, Any

# Number of synthetic users
def synthetic_users(data: pd.DataFrame) -> pd.DataFrame:
    n_users = 1000

    # 1) Username: player0001 ... player1000
    usernames = [f"player{str(i).zfill(4)}" for i in range(1, n_users + 1)]

    # 2) Tagline: '#1234' (4-digit numeric)
    taglines = [f"#{np.random.randint(0, 10000):04d}" for _ in range(n_users)]

    # 3) Join date: random between 2025-01-01 and today
    start_date = pd.to_datetime("2025-01-01")
    end_date = pd.to_datetime("today").normalize()

    random_days = np.random.randint(
        0,
        (end_date - start_date).days + 1,
        size=n_users
    )
    join_dates = start_date + pd.to_timedelta(random_days, unit="D")


    # 4) Rank tier: all start as 'Unranked' (get UUID from competitivetiers data)

    unranked_tier_uuid = data[data['Rank'] == 'UNRANKED']['uuid'].values[0]
    # 4) Build DimUser DataFrame
    df_users = pd.DataFrame({
        "user_id": range(1, n_users + 1),          # surrogate key
        "username": usernames,
        "tagline": taglines,
        "join_date": join_dates,       # all start as Unranked
        "rank_tier_uuid": unranked_tier_uuid
    })
    #df_users['rank_tier_uuid'] = unranked_tier_uuid
    return df_users

