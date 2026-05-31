with source as (
    select * from {{ source('raw', 'round_spike_status') }}
)

select
    match_id,
    round_id,
    (spike_planted = 1) as spike_planted,
    (spike_defused = 1) as spike_defused
from source
