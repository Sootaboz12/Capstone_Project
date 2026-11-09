# NFL Win Probability

CSCI 49900 capstone project for estimating NFL win probability from game situations.
It includes NFL data preparation, a PostgreSQL loader, and a logistic regression
experiment. The React app includes an NFL standings page backed by the FastAPI service.

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
then run `npm ci`, `uv sync --locked`, and `npm run dev` directly. Start the API
in a second terminal with `uv run --locked uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000`.
The Vite development server proxies `/standings` to the API on port 8000, so both
servers must be running to view standings.

## Database

Copy `.env.example` to `.env` and set `DATABASE_URL` to your PostgreSQL connection
URL. Both `postgresql://` and `postgresql+psycopg://` are supported; the app uses
the installed psycopg 3 driver. Keep credentials out of Git.

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

## Notebooks

Run these commands from the repo root after completing the development setup.
Replace `path/to/notebook.ipynb` with your notebook's path. Without the container,
omit `./dev`. Conversion and sync do not execute code.

> [!WARNING]
> Running the model uses substantial resources.

### Convert to Python

```sh
./dev uv run --locked jupytext --to py path/to/notebook.ipynb
```

The generated `.py` file appears beside the notebook with the same base name.

### Keep both files in sync

To keep editing both formats, pair the notebook with a Python file once:

```sh
./dev uv run --locked jupytext --set-formats ipynb,py:percent path/to/notebook.ipynb
```

Then edit either file and sync the pair:

```sh
./dev uv run --locked jupytext --sync path/to/notebook.ipynb
```

Sync uses the more recently modified version to update the pair. You can pass
either file's path. Sync before switching formats or committing; it does not
merge competing edits made to both files.

## Checks

```sh
./dev npm run lint
./dev npm run build
./dev uv lock --check
./dev uv run --locked python -m compileall -q src/db src/model
```

The frontend build writes to `dist/`. There is no automated test suite yet;
these checks do not run the model or verify the database.
