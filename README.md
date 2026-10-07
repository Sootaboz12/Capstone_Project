# NFL Win Probability

CSCI 49900 capstone project for estimating NFL win probability from game situations.
It includes NFL data preparation, a PostgreSQL loader, and a logistic regression
experiment. The React app still uses the starter template and is not connected to either.

## Layout

```text
src/
    app/       React and TypeScript frontend
    db/        NFL data preparation and PostgreSQL loading
    model/     Paired Python script and notebook for model experiments
```

JavaScript and Python project configuration and lockfiles live at the repo root.

## Development

Run all commands from the repo root. The development container provides Node 24,
Python 3.12, uv, and Fish. Install Podman and verify that `podman info` works, then:

```sh
podman build --tag localhost/capstone-dev:latest --file Containerfile.dev .
./dev npm ci
./dev uv sync --locked
./dev dev
```

Open <http://localhost:5173>. Set `PODMAN_DEV_PORT` to use a different host port.
Run `./dev` for an interactive Fish shell or `./dev --help` for command examples.

For development without the container, install Node 24 and uv with Python 3.12,
then run `npm ci`, `uv sync --locked`, and `npm run dev` directly.

## Database

Copy `.env.example` to `.env` and set `DATABASE_URL` to your PostgreSQL connection
URL, using the `postgresql+psycopg://` scheme. Keep credentials out of Git.

Check connectivity:

```sh
./dev uv run --locked ping
```

Load the play-by-play data:

```sh
./dev uv run --locked backend
```

The loader downloads all available seasons using nflreadpy, keeps play events,
and **replaces the `plays` table**. Run it only when you intend to replace that data.

## Model experiments

`src/model/model_testing.py` and `src/model/model_testing.ipynb` are a Jupytext pair.
Edit either file, then sync them before committing. Sync does not execute the model:

```sh
./dev uv run --locked jupytext --sync src/model/model_testing.py
```

> [!WARNING]
> Running the model uses substantial resources.

To run the experiment:

```sh
./dev uv run --locked python src/model/model_testing.py
```

The experiment downloads NFL data and trains logistic regression models without
using the database.

## Checks

```sh
./dev npm run lint
./dev npm run build
./dev uv lock --check
./dev uv run --locked python -m compileall -q src/db src/model
```

The frontend build writes to `dist/`. There is no automated test suite yet;
these checks do not run the model or verify the database.
