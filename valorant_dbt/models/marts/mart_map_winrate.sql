{#
    Per-map activity and outcomes, plus attacker/defender balance from match_status.
#}

with player_match as (
    select * from {{ ref('fct_player_match') }}
),

match_status as (
    select * from {{ ref('stg_match_status') }}
),

map_play as (
    select
        map_id,
        map_name,
        count(*)                                   as player_matches,
        count(distinct match_id)                   as matches,
        round(avg(is_win)::numeric, 4)             as player_win_rate
    from player_match
    group by map_id, map_name
),

map_sides as (
    select
        pm.map_id,
        round(
            sum(ms.attacker_round_wins)::numeric
            / nullif(sum(ms.attacker_round_wins + ms.defender_round_wins), 0),
            4
        ) as attacker_round_win_rate
    from player_match pm
    join match_status ms using (match_id)
    group by pm.map_id
)

select
    mp.map_id,
    mp.map_name,
    mp.matches,
    mp.player_matches,
    mp.player_win_rate,
    ms.attacker_round_win_rate,
    1 - ms.attacker_round_win_rate as defender_round_win_rate
from map_play mp
left join map_sides ms using (map_id)
order by mp.matches desc
