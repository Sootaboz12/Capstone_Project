# Agent context

Read `README.md` for the project layout, setup, and validation commands.

**Running the model requires explicit user permission because it uses substantial
resources.** This includes running experiment scripts, executing model notebook
cells, and importing scripts that run the model at import time. Cleanup, refactoring,
and validation requests do not grant that permission. Syntax checks and Jupytext
synchronization do not execute the model and are allowed.

Keep repo cleanup to layout, documentation, and required path/import updates. The
user does not own subsystem implementations. Preserve source behavior, dependency
lists, package and command names, UI, and notebook contents unless explicitly
asked to change them.

`backend` replaces the `plays` table; do not use it for validation. `ping`
connects to PostgreSQL. Database imports read `DATABASE_URL` and create an engine;
use a dummy URL for offline import checks and do not open a connection.

`src/model/model_testing.py` and `src/model/model_testing.ipynb` are a Jupytext
pair. Sync after editing either file using the README command.
