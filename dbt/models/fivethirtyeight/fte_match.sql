{{
    config(materialized='table')
}}

with

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
    (json ->> 'team1')                            as team1,
    (json ->> 'team2')                            as team2,
    nullif((json ->> 'spi1'), '')::float          as spi1,
    nullif((json ->> 'spi2'), '')::float          as spi2,
    nullif((json ->> 'prob1'), '')::float         as prob1,
    nullif((json ->> 'prob2'), '')::float         as prob2,
    nullif((json ->> 'probtie'), '')::float       as probtie,
    nullif((json ->> 'proj_score1'), '')::float   as proj_score1,
    nullif((json ->> 'proj_score2'), '')::float   as proj_score2,
    nullif((json ->> 'importance1'), '')::float   as importance1,
    nullif((json ->> 'importance2'), '')::float   as importance2,
    nullif((json ->> 'score1'), '')::int          as score1,
    nullif((json ->> 'score2'), '')::int          as score2,
    nullif((json ->> 'xg1'), '')::float           as xg1,
    nullif((json ->> 'xg2'), '')::float           as xg2,
    nullif((json ->> 'nsxg1'), '')::float         as nsxg1,
    nullif((json ->> 'nsxg2'), '')::float         as nsxg2,
    nullif((json ->> 'adj_score1'), '')::float    as adj_score1,
    nullif((json ->> 'adj_score2'), '')::float    as adj_score2
  from unnested

)

select * from fte_match
