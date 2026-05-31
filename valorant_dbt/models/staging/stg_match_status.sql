with source as (
    select * from {{ source('raw', 'match_status') }}
)

select
    match_id,
    attacker_round_wins,
    defender_round_wins,
    attacker_round_wins + defender_round_wins as total_rounds
from source
