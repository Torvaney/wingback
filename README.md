# Wing Back
> Testing team strength models in Python


Because it's backtesting... gettit? Wing _back_? ... Yeah, I'll show myself out.

## Usage

### Initial setup

This project requires **Python 3.8**.

This project is built on top of [`understat-db`](https://github.com/Torvaney/understat-db). The initial setup is the same.

The simplest way to get started is to populate a local database with `docker-compose`.

First, clone the repository:

```bash
git clone https://github.com/Torvaney/understat-db.git
cd understat-db
```

Then, setup the local environment

```bash
make env                  # Create a virtualenv and installs the project & dependencies
source venv/bin/activate  # Activate the virtualenv
cp .env.sample .env       # Copy default environment vars to .env
```

Run the database

```bash
docker-compose up -d db   # Start a postgres database within a docker container
wingback migrate      # Create base database tables
```

Finally, import the data you want

```bash
wingback ingest --leagues EPL --seasons 2020
```

### Backtesting

The xG-based models require match simulations to be present in the database. You can generate these with the `resimulate` command:

```bash
wingback resimulate --leagues EPL --seasons 2020
```

Finally, to backtest the models, you can use the `backtest` command:

```bash
wingback backtest --league EPL --start-date 2021-01-01
```

Note that the full suite of models is very large (see `wingback backtest --help`) and takes a long time to run. You can select specific models using the `--models` flag.

## Requirements

To run this project you will need:

* Python 3.6+
* Docker


## Contributing

Pull requests are encouraged! For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
