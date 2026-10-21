from db.database import engine


def loadb(update_standings):
    update_standings.write_database(
        table_name="standings",
        connection=engine,
        if_table_exists="replace",
        engine="sqlalchemy",
    )
    
