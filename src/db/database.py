import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, make_url

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    database_url = make_url(DATABASE_URL)
    if database_url.drivername == "postgresql":
        database_url = database_url.set(drivername="postgresql+psycopg")
    engine = create_engine(database_url)
else:
    engine = None


def get_engine():
    if engine is None:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it in the environment or .env before using database features."
        )
    return engine