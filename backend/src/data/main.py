from sqlalchemy import text
from nfl_project.database import engine
from nfl_project.process import process_pbp
from nfl_project.loadb import loadb

def main():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(result.scalar())
    
    pbp_plays = process_pbp()

    loadb(pbp_plays)
    print("Finished loading")

if __name__ == "__main__":
    main()