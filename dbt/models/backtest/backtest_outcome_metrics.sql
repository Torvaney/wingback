{{
    config(
      materialized='view',
      tags=['metrics']
    )
}}

with


matches as (

  select * from {{ ref('match') }}

),


backtest_outcomes as (

  select * from {{ ref('backtest_outcome') }}

),


actual_outcomes as (

  select
    *,
    {{ scoreline_to_outcome('home_goals', 'away_goals') }} as outcome
  from matches

)


select
  backtest_outcomes.league_id,
  backtest_outcomes.model,
  count(*)               as n,
  avg(probability)       as avg_probability,
  sum(log(probability))  as ll,
  -sum(log(probability)) as nll
  -- TODO: scoreline nll, scoreline prob, MSE on prematch expected goals
from actual_outcomes
inner join backtest_outcomes
  on backtest_outcomes.match_id = actual_outcomes.id
 and backtest_outcomes.outcome = actual_outcomes.outcome
group by 1, 2
