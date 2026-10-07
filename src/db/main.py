from sqlalchemy import text
from db.database import engine
from db.process import process_pbp
from db.loadb import loadb

def main():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(result.scalar())
        
    pbp_plays = process_pbp()

    loadb(pbp_plays)
    print("Finished loading")
