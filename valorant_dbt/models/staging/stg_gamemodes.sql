with source as (
    select * from {{ source('raw', 'gamemodes_dim') }}
)

select
    uuid        as gamemode_id,
    name        as gamemode_name,
    description,
    duration
from source
