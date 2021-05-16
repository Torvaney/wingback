-- :name fetch_table_names :many
select
  table_name
from information_schema.tables
where table_schema='public'
  and table_type = 'BASE TABLE'


-- :name fetch_shots :many
select * from shot where match_id = :match_id


-- :name fetch_matches :many
select
  match.*,
  home.title as home_team,
  away.title as away_team,
  date_part('day', age(:end, kickoff::date)) as days_ago
from match
join team as home
  on home.id = match.home_team_id
join team as away
  on away.id = match.away_team_id
  -- Supplying None (i.e. NULL) to any of the arguments
  -- will result in the corresponding where clause being
  -- ignored (i.e. it will coalesce to TRUE)
where coalesce(kickoff::date >= :start, true)
  and coalesce(kickoff::date < :end, true)
  and coalesce(league_id in :league_ids, true)
  and coalesce(season_id in :season_ids, true)
order by kickoff
