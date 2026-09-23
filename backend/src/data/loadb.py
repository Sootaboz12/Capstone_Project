from data.database import engine


def loadb(pbp_plays):
    pbp_plays.write_database(
        table_name="plays",
        connection=engine,
        if_table_exists="replace",
        engine="sqlalchemy",
    )