{#
    Per-player credit-economy summary across all rounds the player participated in.
    Grain: one row per user_id.
#}

with economy as (
    select * from {{ ref('stg_weapon_economy') }}
),

players as (
    select * from {{ ref('dim_players') }}
),

agg as (
    select
        user_id,
        count(*)                                            as rounds_played,
        round(avg(credits_start)::numeric, 1)               as avg_credits_start,
        round(avg(spend)::numeric, 1)                       as avg_spend,
        sum(credits_earned)                                 as total_credits_earned,
        sum(spend)                                          as total_credits_spent,
        round(
            avg(case when secondary_weapon <> '' and gear <> '' then 1 else 0 end)::numeric,
            4
        )                                                   as full_buy_rate,
        sum(case when is_pistol_round then 1 else 0 end)    as pistol_rounds_played,
        round(
            sum(case when is_pistol_round and round_won then 1 else 0 end)::numeric
                / nullif(sum(case when is_pistol_round then 1 else 0 end), 0),
            4
        )                                                   as pistol_round_win_rate,
        sum(kills)                                          as total_kills
    from economy
    group by user_id
)

select
    p.user_id,
    p.riot_id,
    a.rounds_played,
    a.avg_credits_start,
    a.avg_spend,
    a.total_credits_earned,
    a.total_credits_spent,
    a.full_buy_rate,
    a.pistol_rounds_played,
    a.pistol_round_win_rate,
    a.total_kills
from agg a
join players p using (user_id)
