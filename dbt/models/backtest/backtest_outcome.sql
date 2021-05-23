{{
    config(materialized='table')
}}

with


backtest_scorelines as (

  select * from {{ ref('backtest_scoreline') }}

),


scorelines_with_outcome as (

  select
    *,
    {{ scoreline_to_outcome('home_goals', 'away_goals') }} as outcome
  from backtest_scorelines

),


outcomes as (

  select
    league_id,
    model,
    date,
    match_id,
    outcome,
    sum(probability) as probability
  from scorelines_with_outcome
  group by 1, 2, 3, 4, 5

)


select * from outcomes order by league_id, model, date, match_id, outcome desc
