from sqlalchemy import text
from data.database import engine
from data.process import process_pbp
from data.loadb import loadb

def main():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(result.scalar())
    
    pbp_plays = process_pbp()

    loadb(pbp_plays)
    print("Finished loading")

if __name__ == "__main__":
    main()