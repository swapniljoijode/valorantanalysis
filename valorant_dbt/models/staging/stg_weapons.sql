with source as (
    select * from {{ source('raw', 'weapons_dim') }}
)

select
    uuid                  as weapon_id,
    name                  as weapon_name,
    category              as weapon_category,
    cost                  as weapon_cost,
    "fireMode"            as fire_mode,
    "fireRate"            as fire_rate,
    "magazineSize"        as magazine_size,
    "runSpeedMultiplier"  as run_speed_multiplier,
    "equipTimeSeconds"    as equip_time_seconds,
    "reloadTimeSeconds"   as reload_time_seconds,
    "firstBulletAccuracy" as first_bullet_accuracy
from source
