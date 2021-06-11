{{
  config(materialized='table')
}}

with


shot as (

  select * from {{ ref('shot') }}

),


match as (

  select * from {{ ref('match') }}

),


shot_totals as (

  select
    match_id,
    count(*) filter (where is_home)     as home_shots,
    count(*) filter (where not is_home) as away_shots,
    sum(xg)  filter (where is_home)     as home_xg,
    sum(xg)  filter (where not is_home) as away_xg
  from shot
  group by 1

),


match_xg  as (

  select
    shot_totals.match_id,
    coalesce(shot_totals.home_shots, 0)::int as home_shots,
    coalesce(shot_totals.away_shots, 0)::int as away_shots,
    coalesce(shot_totals.home_xg, 0)         as home_xg,
    coalesce(shot_totals.away_xg, 0)         as away_xg
  from match
  left join shot_totals
    on shot_totals.match_id = match.id

)


select * from match_xg
