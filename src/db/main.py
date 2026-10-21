from sqlalchemy import text
from db.database import engine
from db.standings import update_standings
from db.loadb import loadb

def main():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(result.scalar())
        
    update = update_standings()

    loadb(update)
    print("Finished loading")

if __name__ == "__main__":
    main()
    