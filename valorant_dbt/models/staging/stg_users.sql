with source as (
    select * from {{ source('raw', 'users_dim') }}
)

select
    user_id,
    username,
    tagline,
    cast(join_date as date) as join_date,
    rank_tier_uuid
from source
