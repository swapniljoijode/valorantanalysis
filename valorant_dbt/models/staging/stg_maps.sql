with source as (
    select * from {{ source('raw', 'maps_dim') }}
)

select
    uuid    as map_id,
    name    as map_name,
    "Icon"  as icon_url
from source
