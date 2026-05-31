{#
    Current rank distribution: each player's rank after their most recent match.
#}

with player_match as (
    select * from {{ ref('fct_player_match') }}
),

latest as (
    select
        user_id,
        rank_after,
        points_after,
        row_number() over (
            partition by user_id
            order by match_date desc, match_id desc
        ) as rn
    from player_match
)

select
    rank_after                                          as current_rank,
    count(*)                                            as players,
    round(count(*)::numeric / sum(count(*)) over (), 4) as share_of_players,
    round(avg(points_after)::numeric, 1)                as avg_points
from latest
where rn = 1
group by rank_after
order by players desc
