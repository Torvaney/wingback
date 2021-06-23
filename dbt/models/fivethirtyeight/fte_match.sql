{{
    config(materialized='table')
}}

with


team_map as (

  select * from {{ ref('team_map') }}

),


unnested as (

  select
    json_array_elements(json) as json
  from base_fivethirtyeight

),


fte_match as (

  select

    (json ->> 'season')::text                     as season,  -- Use text, so that it lines up with Understat
    (json ->> 'date')::date                       as date,
    (json ->> 'league_id')::int                   as league_id,
    (json ->> 'league')                           as league,
    (json ->> 'team1')                            as home_team,
    (json ->> 'team2')                            as away_team,
    nullif((json ->> 'score1'), '')::int          as home_goals,
    nullif((json ->> 'score2'), '')::int          as away_goals,
    nullif((json ->> 'spi1'), '')::float          as home_spi,
    nullif((json ->> 'spi2'), '')::float          as away_spi,
    nullif((json ->> 'prob1'), '')::float         as p_home_win,
    nullif((json ->> 'probtie'), '')::float       as p_draw,
    nullif((json ->> 'prob2'), '')::float         as p_away_win,
    nullif((json ->> 'proj_score1'), '')::float   as home_proj_score,
    nullif((json ->> 'proj_score2'), '')::float   as away_proj_score,
    nullif((json ->> 'importance1'), '')::float   as home_importance,
    nullif((json ->> 'importance2'), '')::float   as away_importance,
    nullif((json ->> 'xg1'), '')::float           as home_xg,
    nullif((json ->> 'xg2'), '')::float           as away_xg,
    nullif((json ->> 'nsxg1'), '')::float         as home_nsxg,
    nullif((json ->> 'nsxg2'), '')::float         as away_nsxg,
    nullif((json ->> 'adj_score1'), '')::float    as home_adj_score,
    nullif((json ->> 'adj_score2'), '')::float    as away_adj_score
  from unnested

),


joined_match as (

  select
    home_map.understat_id as home_team_id,
    away_map.understat_id as away_team_id,
    fte_match.*
  from fte_match
  left join team_map as home_map
    on home_map.fivethirtyeight_name = fte_match.home_team
  left join team_map as away_map
    on away_map.fivethirtyeight_name = fte_match.away_team

)


select * from joined_match order by date
