with source as (
    select * from {{ source('raw', 'gears_dim') }}
)

select
    uuid                as gear_id,
    name                as gear_name,
    description,
    cost,
    "damageReduction"   as damage_reduction,
    "damageAbsorbtion"  as damage_absorption,
    "regenPool"         as regen_pool
from source
