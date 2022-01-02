-- :name fetch_table_names :many
select
  table_name
from information_schema.tables
where table_schema='public'
  and table_type = 'BASE TABLE'


-- :name fetch_shots :many
select * from shot where match_id = :match_id


-- :name fetch_matchdays :many
select distinct
  kickoff::date as "date"
from match
  -- Supplying None (i.e. NULL) to any of the arguments
  -- will result in the corresponding where clause being
  -- ignored (i.e. it will coalesce to TRUE)
where coalesce(kickoff::date >= :start, true)
  and coalesce(kickoff::date < :end, true)
  and coalesce(league_id = :league_id, true)
  -- Constant clauses
  and is_result = true
order by "date"


-- :name fetch_matches :many
select
  match.*,
  match_xg.home_xg as naive_home_xg,
  match_xg.away_xg as naive_away_xg,
  home.title as home_team,
  away.title as away_team,
  (:end)::date - kickoff::date as days_ago
from match
join team as home
  on home.id = match.home_team_id
join team as away
  on away.id = match.away_team_id
left join match_xg
  on match_xg.match_id = match.id
  -- Supplying None (i.e. NULL) to any of the arguments
  -- will result in the corresponding where clause being
  -- ignored (i.e. it will coalesce to TRUE)
where coalesce(kickoff::date >= :start, true)
  and coalesce(kickoff::date < :end, true)
  and coalesce(league_id in :league_ids, true)
  and coalesce(season_id in :season_ids, true)
  -- Constant clauses
  and is_result = true
order by kickoff


-- :name fetch_resimulations :many
select
  resimulation.*,
  match.home_team_id,
  match.away_team_id
from resimulation
join match
  on match.id = resimulation.match_id
where match_id in :match_ids
  and probability >= :min_probability
order by match.kickoff


-- :name fetch_backtest :one
select *
from base_backtest
where model = :model
  and league_id in :league_ids
  and date = (:date)::date
limit 1


-- :name fetch_team :one
select *
from team
where id = :team_id


-- :name fetch_all_matches :many
select
  match.*,
  home.title as home_team,
  away.title as away_team
from match
join team as home
  on home.id = match.home_team_id
join team as away
  on away.id = match.away_team_id
where coalesce(league_id in :league_ids, true)
  and coalesce(season_id in :season_ids, true)
order by kickoff
