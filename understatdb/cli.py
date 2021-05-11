# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/cli.ipynb (unless otherwise specified).

__all__ = ['app', 'migrate', 'build_tables', 'ingest']

# Cell
import os
import functools
import itertools
import pathlib
import typing
import time

import dbt.main
import dotenv
import playhouse.postgres_ext
import pyprojroot
import typer

import understatdb


app = typer.Typer()

# Internal Cell


def initialize_db():
    # Load database config from environment
    postgres_db = playhouse.postgres_ext.PostgresqlExtDatabase(
        host=os.environ['DB_HOST'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASS'],
        database=os.environ['DB_NAME'],
        port=os.environ['DB_PORT'],
    )

    # Configure proxy database to use configured postgres
    typer.secho('Initialising database connection...', fg=typer.colors.BRIGHT_BLACK)
    understatdb.db.DB.initialize(postgres_db)

# Cell


@app.command()
def migrate(interactive: bool = True):
    """ Migrate database to the current schema (as defined in nbs/db.ipynb) """

    initialize_db()

    # Migrate database tables
    typer.secho('Migrating database tables...', fg=typer.colors.BRIGHT_BLACK)
    understatdb.db.DB.evolve(
        ignore_tables=understatdb.db.EVOLVE_IGNORE_TABLES,
        interactive=interactive
    )
    typer.secho('Done!', fg=typer.colors.GREEN, bold=True)

# Cell


@app.command()
def build_tables(args: typing.List[str] = typer.Option([], help='Additional arguments passed to `dbt run`')):
    """ Build tables from base data using dbt """

    project_dir = pyprojroot.here()/'dbt'
    profiles_dir = pyprojroot.here()/'.dbt'

    base_args = [
        'run',
        '--profiles-dir',
        str(profiles_dir),
        '--project-dir',
        str(project_dir)
    ]

    # NOTE: Python API is not officially supported, so
    # watch out if you change dbt versions...
    _ = dbt.main.handle_and_check(base_args + list(args))

# Cell


_DEFAULT_INGEST_LEAGUES = [l.value for l in understatdb.understat.League]
_DEFAULT_INGEST_SEASONS = list(range(2014, 2021))


@app.command()
def ingest(
    refresh: bool = False,
    leagues: typing.List[str] = typer.Option(_DEFAULT_INGEST_LEAGUES, help='Leagues to import'),
    seasons: typing.List[int] = typer.Option(_DEFAULT_INGEST_SEASONS, help='Seasons to import (by start year)'),
):
    """ Ingest match and shot data from Understat.com """

    initialize_db()
    client = understatdb.understat.Understat()

    for league, season in itertools.product(
        [understatdb.understat.League(l) for l in leagues],
        seasons
    ):
        # Add league & season to DB
        with understatdb.db.DB.atomic():
            db_league, _ = understatdb.db.League.get_or_create(name=league.value)
            db_season, _ = understatdb.db.Season.get_or_create(name=season)

        # Check if a record for this league and season already exists. If so, skip it.
        existing_record = understatdb.db.Matches.get_or_none(
            league_id=db_league.id,
            season_id=db_season.id
        )
        if not refresh and existing_record:
            typer.secho(
                f'Data for {league.value}, {season} already exists. Skipping. '
                'To update data for this league and season, use the `--refresh` flag',
                fg=typer.colors.BRIGHT_BLACK
            )
            continue

        # Add match and shot data to DB
        typer.secho(f'Ingesting data for {league.value}, {season}', fg=typer.colors.BLUE)
        with understatdb.db.DB.atomic():

            # Fetch match data from understat
            matches = client.matches(league, season)

            # Delete any old match data
            if refresh:
                understatdb.db.Matches.delete().where(
                    (understatdb.db.Matches.league_id==db_league.id) &
                    (understatdb.db.Matches.season_id==db_season.id)
                ).execute()

            db_matches = understatdb.db.Matches.create(
                league_id=db_league.id,
                season_id=db_season.id,
                json=matches,
                version=understatdb.__version__
            )

            with typer.progressbar(matches, label="Shots") as progress:
                for match in progress:
                    if not match['isResult']:
                        continue

                    # Add an artificial crawl delay to avoid bombarding
                    # understat with requests
                    # There's no robots.txt or ToS available on the site,
                    # So we just use a relatively conservative delay of
                    # 5 seconds per (shots) request
                    time.sleep(5)

                    match_id = int(match['id'])
                    shots = client.shots(match_id)

                    # Delete any old shots data
                    if refresh:
                        understatdb.db.Shots.delete().where(
                            understatdb.db.Shots.match_id==match_id
                        ).execute()

                    db_shots = understatdb.db.Shots.create(
                        match_id=match_id,
                        json=shots,
                        version=understatdb.__version__
                    )

        # Rebuild tables in dbt
        build_tables(args=[])

# Cell

# Try/except block seems to be the 'canonical'
# way to export __name__ == __main__ in nbdev.
# By excepting an ImportError, we don't have to
# include nbdev as a runtime dependency (only a
# development dependency).
#
# See:
#  * https://pete88b.github.io/fastpages/nbdev/fastai/jupyter/2020/07/24/nbdev-deep-dive.html#Export-a-if-__name__-==-
#  * https://forums.fast.ai/t/nbdev-is-there-a-way-to-export-a-if-name-main-clause/73050/3
try:
    from nbdev.imports import IN_NOTEBOOK
except ImportError:
    IN_NOTEBOOK = False

if __name__ == '__main__' and not IN_NOTEBOOK:
    dotenv.load_dotenv()
    app()