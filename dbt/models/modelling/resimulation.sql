{{
    config(materialized='table')
}}

with


resim_json as (

  select
    match_id,
    json_array_elements(json) as json
  from base_resimulation

),


resim as (

  select
    match_id,
    (json ->> 'home_goals')::int as home_goals,
    (json ->> 'away_goals')::int as away_goals,
    (json ->> 'probability')::float as probability
  from resim_json
)


select * from resim
