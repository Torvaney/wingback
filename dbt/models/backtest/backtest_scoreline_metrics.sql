{{
    config(
      materialized='table',
      tags=['metrics']
    )
}}

with


matches as (

  select * from {{ ref('match') }}

),


backtest_scorelines as (

  select * from {{ ref('backtest_scoreline') }}

)


select
  backtest_scorelines.league_id,
  backtest_scorelines.model,
  count(*)               as n,
  avg(probability)       as avg_probability,
  sum(log(probability))  as ll,
  -sum(log(probability)) as nll
from matches
inner join backtest_scorelines
  on backtest_scorelines.match_id = matches.id
 and backtest_scorelines.home_goals = matches.home_goals
 and backtest_scorelines.away_goals = matches.away_goals
group by 1, 2
