from db.database import engine


# stores the engines that loads dataframes into the database

def load_standings(update_standings):
    update_standings.write_database(
        table_name="standings",
        connection=engine,
        if_table_exists="replace",
        engine="sqlalchemy",
    )
    

def load_u(update_standings):
    update_standings.create_database(
        table_name="standings",
        connection=engine,
        if_table_exists="replace",
        engine="sqlalchemy",
    )

