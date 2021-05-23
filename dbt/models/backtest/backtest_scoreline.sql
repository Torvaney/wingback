{{
    config(
      materialized='incremental',
      post_hooks=[
        create_index(this, 'league_id'),
        create_index(this, 'model'),
        create_index(this, 'date'),
      ]
    )
}}


with


base_backtest_inc as (

  select
    base_backtest.*
  from base_backtest

  {% if is_incremental() %}
    left join {{ this }} as existing
      using (league_id, model, date)
    where existing.league_id is null  -- i.e. hasn't been created yet (`league_id` isn't important, could be any column)
  {% endif %}

),


backtest_matches_json as (

  select
    league_id,
    model,
    date,
    json_array_elements((json -> 'predictions')) as json
  from base_backtest_inc
),


backtest_scorelines_json as (

  select
    league_id,
    model,
    date,
    (json ->> 'match_id')::int as match_id,
    json_array_elements((json -> 'scorelines')) as scorelines
  from backtest_matches_json

),


backtest_scorelines as (

  select
    league_id,
    model,
    date,
    match_id,
    (scorelines ->> 'home_goals')::int     as home_goals,
    (scorelines ->> 'away_goals')::int     as away_goals,
    (scorelines ->> 'probability')::float  as probability
  from backtest_scorelines_json

)

select * from backtest_scorelines
