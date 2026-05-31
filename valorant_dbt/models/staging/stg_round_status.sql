with source as (
    select * from {{ source('raw', 'round_status') }}
)

select
    match_id,
    round_id,
    total_round_duration
from source
