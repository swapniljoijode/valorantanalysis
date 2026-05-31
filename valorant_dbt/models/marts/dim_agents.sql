select
    agent_id,
    agent_name,
    role,
    is_playable,
    abilities_count
from {{ ref('stg_agents') }}
