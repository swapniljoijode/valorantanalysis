with source as (
    select * from {{ source('raw', 'agents_dim') }}
)

select
    uuid                as agent_id,
    name                as agent_name,
    role                as role,
    "isPlayable"        as is_playable,
    "abilitiesCount"    as abilities_count,
    ability1,
    ability2,
    ability3,
    "Ultimate"          as ultimate
from source
