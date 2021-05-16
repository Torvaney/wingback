# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/db.ipynb (unless otherwise specified).

__all__ = ['DB', 'queries', 'evolve_ignore', 'prefixed_snake_case', 'EVOLVE_IGNORE_TABLES', 'BaseModel', 'League',
           'Season', 'Matches', 'Shots', 'Resimulation']

# Cell
import functools

import peewee
import peeweedbevolve
import playhouse.postgres_ext
import pugsql
import pyprojroot


DB = peewee.DatabaseProxy()

# Cell

queries = pugsql.module(pyprojroot.here()/'sql')

# Cell

EVOLVE_IGNORE_TABLES = []


def evolve_ignore(cls, registry=EVOLVE_IGNORE_TABLES):
    registry.append(cls._meta.table_name)
    return cls


def prefixed_snake_case(prefix, cls):
    return prefix + peewee.make_snake_case(cls.__name__)

# Cell


@evolve_ignore
class BaseModel(peewee.Model):
    """
    A model for base (json) data from Understat
    """
    class Meta:
        database = DB
        legacy_table_names = False
        table_function = functools.partial(prefixed_snake_case, 'base_')

# Cell


class League(BaseModel):
    id = peewee.PrimaryKeyField()
    name = peewee.TextField()

# Cell


class Season(BaseModel):
    id = peewee.PrimaryKeyField()
    name = peewee.TextField()

# Cell


class Matches(BaseModel):
    id = peewee.PrimaryKeyField()

    # Since we're ingesting the data before reshaping
    # and testing with dbt (ELT not ETL), we might prefer
    # flexibility to the correctness that a FK provides.
    # But since understat don't actually provide any
    # IDs (afaik, it's all indexed by league *name*),
    # we're going to be making our own IDs at some point
    # anyway. So I prefer to do that with the guarantees
    # of a FK.
    league_id = peewee.ForeignKeyField(League)

    # Similar logic to above (`league_id`),
    # we're creating our own season IDs.
    # Understat indexes by season start year,
    # so we could conceivably just use an
    # integer field and refactor if that assumption
    # is ever violated.
    season_id = peewee.ForeignKeyField(Season)

    # Dump the scraped JSON as JSON
    # We'll clean it up in dbt
    json = playhouse.postgres_ext.JSONField()

    # Store the app version, so that we can parse
    # the JSON differently should the format change in
    # the future.
    version = peewee.TextField()

    class Meta:
        indexes = (
            # Force uniqueness on the combination of
            # league and season ID.
            # We should only ever have one row per
            # league, per season!
            (('league_id', 'season_id'), True),
        )

# Cell


class Shots(BaseModel):
    id = peewee.PrimaryKeyField()

    # This time, we're using Understat's IDs,
    # so we aren't interested in using a FK for
    # match ID.
    match_id = peewee.IntegerField(unique=True)

    # Dump the scraped JSON as JSON again
    json = playhouse.postgres_ext.JSONField()

    version = peewee.TextField()

# Cell


class Resimulation(BaseModel):
    id = peewee.PrimaryKeyField()
    match_id = peewee.IntegerField(unique=True)
    json = playhouse.postgres_ext.JSONField()
    version = peewee.TextField()