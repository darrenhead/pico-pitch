import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client() -> Client:
    """Initializes and returns the Supabase client."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Supabase URL and Key must be set in the environment variables.")
    return create_client(url, key)

if __name__ == '__main__':
    try:
        supabase = get_supabase_client()
        print("Supabase client created successfully.")
        # Example: Fetching user to test connection (requires auth setup)
        # print(supabase.auth.get_user())
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}") 