with source as (
    select * from {{ source('raw', 'match_df') }}
)

select
    match_id,
    cast(match_date as timestamp) as match_date,
    user_id,
    agent_id,
    agent_name,
    map_id,
    map_name,
    "team A"    as team_a_score,
    "team B"    as team_b_score
from source
