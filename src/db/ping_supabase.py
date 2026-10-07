from sqlalchemy import text
from db.database import engine

def main():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        print("Supabase ping successful")
        
if __name__ == "__main__":
    main()