from sqlalchemy import text
from db.database import get_engine
from db.standings import update_standings
from db.loadb import load_standings

# creates the tables


def update_standings_table():
    with get_engine().connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(result.scalar())
        
    update = update_standings()

    load_standings(update)
    print("Finished loading")


# def create_users_table():
#     with engine.begin() as conn:
#         conn.execute(
#             text("""
#                 CREATE TABLE IF NOT EXISTS public.profiles (
#                 id UUID PRIMARY KEY 
#                 REFERENCES auth.users(id)
#                 ON DELETE CASCADE,
#                 username TEXT UNIQUE,n
#                 display_name TEXT
#                 );
#             """)
#         )

def create_predictions_table():
    
    with get_engine().begin() as conn:
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS predictions (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES auth.users(id),
                game_state JSONB NOT NULL,
                play_predictions JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
        )

if "__main__" == __name__:
    update_standings_table()