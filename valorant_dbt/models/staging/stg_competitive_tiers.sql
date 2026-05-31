with source as (
    select * from {{ source('raw', 'competitive_tiers_dim') }}
)

{# NOTE: `uuid` here is the episode's tier-table id (identical for every row),
   not a per-rank key. The natural key for a rank tier is the rank name. #}
select
    "Rank"      as rank_name,
    "Episode"   as episode,
    uuid        as episode_id,
    "Icon"      as icon_url
from source
