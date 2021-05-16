# Wing Back
> Testing team strength models in Python


Because it's backtesting... gettit? Wing _back_? I'll show myself out.

## Usage

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
understat-db migrate      # Create base database tables
```

Finally, import the data you want

```bash
understat-db ingest --leagues EPL --seasons 2020
```

## Requirements

To run this project you will need:

* Python 3.6+
* Docker


## Contributing

Pull requests are encouraged! For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
