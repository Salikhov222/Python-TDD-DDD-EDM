from dotenv import load_dotenv
import os

load_dotenv()

def get_postgres_uri():
    host = os.getenv("DB_HOST")    
    port = 5432
    password = os.getenv("DB_PASSWORD")
    user, db_name = 'allocation', 'allocation'
    return f'postgresql://{user}:{password}@{host}:{port}/{db_name}'


def get_api_url():
    host = os.getenv("API_HOST")
    port = 8000
    return f"http://{host}:{port}"


def get_redis_host_and_port():
    host = os.getenv("REDIS_HOST")
    port = 6379
    return dict(host=host, port=port)
