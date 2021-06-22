# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/cli.ipynb (unless otherwise specified).

__all__ = ['EnvTyper', 'app', 'migrate', 'build_tables', 'ingest', 'ingest_538', 'resimulate', 'backtest']

# Internal Cell
import dataclasses
import datetime as dt
import functools
import itertools
import os
import pathlib
import typing
import time

import dbt.main
import dotenv
import playhouse.postgres_ext
import pyprojroot
import typer

import wingback

# Cell


class EnvTyper(typer.Typer):
    """
    Just like typer.Typer, except it loads the environment with
    `dotenv.load_dotenv` before executing any command.
    """
    def __call__(self, *args, **kwargs):
        dotenv.load_dotenv()
        return super().__call__(*args, **kwargs)



app = EnvTyper()

# Internal Cell


def initialize_db():
    """
    Load database config from environment and initialise
    `understatdb.db.DB` with a database connection.
    """

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
    wingback.db.DB.initialize(postgres_db)

    # Connect pugsql to database
    wingback.db.queries.connect('postgresql://{user}:{password}@{host}:{port}/{database}'.format(
        host=os.environ['DB_HOST'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASS'],
        database=os.environ['DB_NAME'],
        port=os.environ['DB_PORT'],
    ))

# Cell


@app.command()
def migrate(interactive: bool = True):
    """ Migrate database to the current schema (as defined in nbs/db.ipynb) """

    initialize_db()

    # Get names of tables generated by dbt and exclude them from the migration
    dbt_models_path = pyprojroot.here()/'dbt'/'models'
    dbt_tables = [f.stem for f in dbt_models_path.glob('**/*.sql')]

    # Migrate database tables
    typer.secho('Migrating database tables...', fg=typer.colors.BRIGHT_BLACK)
    wingback.db.DB.evolve(
        ignore_tables=wingback.db.EVOLVE_IGNORE_TABLES + dbt_tables,
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
    typer.secho('Building tables with dbt', fg=typer.colors.BLUE)
    _ = dbt.main.handle_and_check(base_args + list(args))

# Cell


_DEFAULT_INGEST_LEAGUES = [l.value for l in wingback.understat.League]
_DEFAULT_INGEST_SEASONS = list(range(2014, 2021))


@app.command()
def ingest(
    refresh: bool = False,
    leagues: typing.List[str] = typer.Option(
        _DEFAULT_INGEST_LEAGUES,
        help='Leagues to import',
        callback=lambda xs: [wingback.understat.League(x) for x in xs]
    ),
    seasons: typing.List[int] = typer.Option(
        _DEFAULT_INGEST_SEASONS,
        help='Seasons to import (by start year)'
    ),
):
    """ Ingest match and shot data from Understat.com """

    initialize_db()
    client = wingback.understat.Understat()

    for league, season in itertools.product(leagues, seasons):
        # Add league & season to DB
        with wingback.db.DB.atomic():
            db_league, _ = wingback.db.League.get_or_create(name=league.value)
            db_season, _ = wingback.db.Season.get_or_create(name=season)

        # Check if a record for this league and season already exists. If so, skip it.
        existing_record = wingback.db.Matches.get_or_none(
            league_id=db_league.id,
            season_id=db_season.id
        )
        if (not refresh) and existing_record:
            typer.secho(
                f'Data for {league.value}, {season} already exists. Skipping. '
                'To update data for this league and season, use the `--refresh` flag',
                fg=typer.colors.BRIGHT_BLACK
            )
            continue

        # Add match and shot data to DB
        typer.secho(f'Ingesting data for {league.value}, {season}', fg=typer.colors.BLUE)
        with wingback.db.DB.atomic():

            # Fetch match data from understat
            matches = client.matches(league, season)

            # Delete any old match data
            if refresh:
                wingback.db.Matches.delete().where(
                    (wingback.db.Matches.league_id==db_league.id) &
                    (wingback.db.Matches.season_id==db_season.id)
                ).execute()

            db_matches = wingback.db.Matches.create(
                league_id=db_league.id,
                season_id=db_season.id,
                json=matches,
                version=wingback.__version__
            )

            with typer.progressbar(matches, label='Shots') as progress:
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
                        wingback.db.Shots.delete().where(
                            wingback.db.Shots.match_id==match_id
                        ).execute()

                    db_shots = wingback.db.Shots.create(
                        match_id=match_id,
                        json=shots,
                        version=wingback.__version__
                    )

    # Rebuild tables in dbt
    build_tables(args=['--models', 'understat'])

# Cell


@app.command()
def ingest_538(
    refresh: bool = False
):
    """ Ingest match and shot data from fivethirtyeight.com """

    initialize_db()

    # Only import if refreshing or if no 538 data already exists
    if refresh or not list(wingback.db.Fivethirtyeight.select().execute()):
        with wingback.db.DB.atomic():
            wingback.db.Fivethirtyeight.delete().execute()

            __ = wingback.db.Fivethirtyeight.create(
                json=wingback.fivethirtyeight.fetch_data()
            )

    # Rebuild tables in dbt
    build_tables(args=['--models', 'fivethirtyeight'])

# Cell


@app.command()
def resimulate(
    refresh: bool = False,
    leagues: typing.List[str] = typer.Option(
        _DEFAULT_INGEST_LEAGUES,
        help='Leagues to import',
        callback=lambda xs: [wingback.understat.League(x) for x in xs]
    ),
    seasons: typing.List[int] = typer.Option(
        _DEFAULT_INGEST_SEASONS,
        help='Seasons to import (by start year)'
    ),
):
    """ Resimulate matches based on individual shot xGs """
    initialize_db()

    for league, season in itertools.product(leagues, seasons):
        # TODO: handle case where no league exists
        league_id = wingback.db.League.get(name=league.value).id
        season_id = wingback.db.Season.get(name=season).id
        matches = list(wingback.db.queries.fetch_matches(
            league_ids=[league_id],
            season_ids=[season_id],
            start=None,
            end=None
        ))

        typer.secho(f'Resimulating matches for {league.value}, {season}', fg=typer.colors.BLUE)
        with typer.progressbar(matches, label='Matches') as progress:
            for match in progress:
                # Check if match is already resimulated and skip if so
                if (not refresh) and wingback.db.Resimulation.get_or_none(match_id=match['id']):
                    continue

                shots = list(wingback.db.queries.fetch_shots(match_id=match['id']))
                resims = wingback.resimulation.resimulate_match(shots)

                with wingback.db.DB.atomic():
                    # Delete any old resim data
                    if refresh:
                        wingback.db.Resimulation.delete().where(
                            wingback.db.Resimulation.match_id==match['id']
                        ).execute()

                    db_resim = wingback.db.Resimulation.create(
                        match_id=match['id'],
                        json=resims,
                        version=wingback.__version__
                    )

    build_tables(args=['--models', 'resimulation'])

# Cell


@app.command()
def backtest(
    refresh: bool = False,
    models: typing.List[str] = typer.Option(
        list(wingback.team_strength.MODEL_REGISTRY.keys()),
        help='Models to fit',
    ),
    # Because there's no overlap across leagues in the understat dataset
    # just pick one league at a time
    league: str = typer.Option(
        'EPL',
        help='League to run team-strength model on',
        callback=lambda x: wingback.understat.League(x)
    ),
    start_date: str = typer.Option(
        '2015-07-01',
        help='Start fitting the model from a certain date',
        callback=lambda x: dt.datetime.strptime(x, '%Y-%m-%d').date()
    )
):
    """ Fit team strength model(s) and persist to database """
    initialize_db()

    db_league = wingback.db.League.get_or_none(name=league.value)
    if not db_league:
        raise ValueError(f'No data for "{league}" found. Do you need to import the data?')
    league_id = db_league.id

    matchdays = list(wingback.db.queries.fetch_matchdays(
        league_id=league_id,
        start=start_date,
        end=None
    ))
    typer.secho(f'Found {len(matchdays)} {league.value} matchdays from {start_date}', fg=typer.colors.BLUE)

    typer.secho(f'Backtesting models...', fg=typer.colors.BRIGHT_BLACK)
    for model_name in models:
        model = wingback.team_strength.MODEL_REGISTRY[model_name]

        with typer.progressbar(matchdays, label=model_name) as progress:
            for matchday in progress:
                date = matchday['date']

                # Check if record exists...
                if (not refresh) and wingback.db.Backtest.get_or_none(
                    model=model_name,
                    league_id=league_id,
                    date=date
                ):
                    continue

                # Fit the model
                train = model.fetch_data([league_id], date)
                model.fit(train)

                # Fetch the days' matches to test the model
                test = list(wingback.db.queries.fetch_matches(
                    start=date,
                    end=date+dt.timedelta(days=1),
                    league_ids=[league_id],
                    season_ids=[None]
                ))

                # Make predictions for that matchday
                predictions = model.predict(test)

                # Save model and predictions to database
                with wingback.db.DB.atomic():
                    # Delete any existing records if `refresh`...
                    if refresh:
                        wingback.db.Backtest.delete().where(
                            wingback.db.Backtest.model==model_name,
                            wingback.db.Backtest.league_id==league_id,
                            wingback.db.Backtest.date==date,
                        ).execute()

                    wingback.db.Backtest.create(
                        model=model_name,
                        league_id=league_id,
                        date=date,
                        json={
                            'model': model_name,
                            'parameters': model.to_dict(),
                            'predictions': [
                                {'match_id': match['id'],
                                 'scorelines': [dataclasses.asdict(p) for p in preds]}
                                for match, preds in zip(test, predictions)
                            ],
                        },
                        version=wingback.__version__
                    )

    # Rebuild tables in dbt
    build_tables(args=['--models', 'backtest'])

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
    app()