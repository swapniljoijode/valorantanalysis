{#
    Player dimension. NOTE: users.rank_tier_uuid is an episode reference, not a
    per-rank key, so it is carried as an attribute only. A player's actual rank
    lives in rank_history (every player starts UNRANKED).
#}

select
    user_id,
    username,
    tagline,
    username || tagline as riot_id,
    join_date,
    rank_tier_uuid
from {{ ref('stg_users') }}
