with source as (
    select * from {{ source('raw', 'match_summary') }}
)

select
    match_id,
    agent_name,
    total_kills,
    total_deaths,
    total_assists,
    first_bloods,
    total_damage_dealt,
    total_plants,
    total_deffused      as total_defused,
    "ACV"               as avg_combat_value
from source
