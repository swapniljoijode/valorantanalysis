select
    map_id,
    map_name
from {{ ref('stg_maps') }}
