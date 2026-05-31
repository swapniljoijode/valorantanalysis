{#
    Per-player career performance summary across all matches.
#}

with player_match as (
    select * from {{ ref('fct_player_match') }}
),

players as (
    select * from {{ ref('dim_players') }}
),

agg as (
    select
        user_id,
        count(*)                              as matches_played,
        sum(is_win)                           as wins,
        count(*) - sum(is_win)                as losses,
        round(sum(is_win)::numeric / count(*), 4) as win_rate,
        sum(total_kills)                      as total_kills,
        sum(total_deaths)                     as total_deaths,
        sum(total_assists)                    as total_assists,
        sum(first_bloods)                     as total_first_bloods,
        round(
            (sum(total_kills) / nullif(sum(total_deaths), 0))::numeric,
            3
        )                                     as kd_ratio,
        round(avg(avg_combat_score)::numeric, 1) as avg_combat_score
    from player_match
    group by user_id
),

current_rank as (
    select user_id, rank_after
    from (
        select
            user_id,
            rank_after,
            row_number() over (
                partition by user_id
                order by match_date desc, match_id desc
            ) as rn
        from player_match
    ) ranked
    where rn = 1
)

select
    p.user_id,
    p.riot_id,
    cr.rank_after as current_rank,
    a.matches_played,
    a.wins,
    a.losses,
    a.win_rate,
    a.total_kills,
    a.total_deaths,
    a.total_assists,
    a.total_first_bloods,
    a.kd_ratio,
    a.avg_combat_score
from agg a
join players p using (user_id)
left join current_rank cr using (user_id)
