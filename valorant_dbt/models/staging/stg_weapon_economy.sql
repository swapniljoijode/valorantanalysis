with source as (
    select * from {{ source('raw', 'weapon_economy') }}
)

select
    match_id,
    round_id,
    round_number,
    user_id,
    agent_name,
    team,
    side,
    is_pistol_round,
    carried_loadout,
    credits_start,
    sidearm,
    sidearm_cost,
    secondary_weapon,
    secondary_cost,
    gear,
    gear_cost,
    spend,
    credits_end,
    kills,
    survived,
    round_won,
    spike_planted,
    credits_earned,
    loss_streak
from source
