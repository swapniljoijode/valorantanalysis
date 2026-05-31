{#
    Player-match fact. Grain: one row per player per match.
    Combines participation (stg_matches), per-agent combat stats
    (stg_match_summary, joined on match_id + agent_name) and rank
    movement (stg_rank_history, joined on match_id + user_id).
#}

with matches as (
    select * from {{ ref('stg_matches') }}
),

summary as (
    select * from {{ ref('stg_match_summary') }}
),

rank_history as (
    select * from {{ ref('stg_rank_history') }}
)

select
    m.match_id || '-' || m.user_id  as match_player_id,
    m.match_id,
    m.user_id,
    m.match_date,
    m.agent_id,
    m.agent_name,
    m.map_id,
    m.map_name,
    m.team_a_score,
    m.team_b_score,

    r.result,
    r.team_rounds_won,
    r.team_rounds_lost,
    case when r.result = 'win' then 1 else 0 end as is_win,

    s.total_kills,
    s.total_deaths,
    s.total_assists,
    s.first_bloods,
    s.total_damage_dealt,
    s.total_plants,
    s.total_defused,
    s.avg_combat_value,

    r.avg_combat_score,
    r.radiant_delta,
    r.rank_before,
    r.points_before,
    r.rank_after,
    r.points_after
from matches m
left join summary s
    on m.match_id = s.match_id and m.agent_name = s.agent_name
left join rank_history r
    on m.match_id = r.match_id and m.user_id = r.user_id
