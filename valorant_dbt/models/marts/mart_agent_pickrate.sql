{#
    Agent popularity and effectiveness across all player-matches.
#}

with player_match as (
    select * from {{ ref('fct_player_match') }}
),

total as (
    select count(*) as total_player_matches from player_match
)

select
    pm.agent_name,
    count(*)                                   as times_picked,
    round(count(*)::numeric / t.total_player_matches, 4) as pick_rate,
    sum(pm.is_win)                             as wins,
    round(sum(pm.is_win)::numeric / count(*), 4) as win_rate,
    round(avg(pm.avg_combat_score)::numeric, 1) as avg_combat_score,
    round(
        (sum(pm.total_kills) / nullif(sum(pm.total_deaths), 0))::numeric,
        3
    )                                          as kd_ratio
from player_match pm
cross join total t
group by pm.agent_name, t.total_player_matches
order by times_picked desc
