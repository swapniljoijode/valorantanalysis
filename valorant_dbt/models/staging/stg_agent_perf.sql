with source as (
    select * from {{ source('raw', 'agent_perf_status') }}
)

select
    match_id,
    round_id,
    agent_name,
    ("isAttacker" = 1)  as is_attacker,
    ("isDefender" = 1)  as is_defender,
    opponent,
    outgoing_head_damage,
    outgoing_body_damage,
    outgoing_leg_damage,
    incoming_head_damage,
    incoming_body_damage,
    incoming_leg_damage,
    cast(killed as integer)      as kills,
    cast(death as integer)       as deaths
from source
