with source as (
    select * from {{ source('raw', 'rank_history') }}
)

select
    match_id,
    user_id,
    agent_name,
    result,
    team_rounds_won,
    team_rounds_lost,
    avg_combat_score,
    team_acs_mean,
    radiant_delta,
    rank_before,
    points_before,
    rank_after,
    points_after
from source
