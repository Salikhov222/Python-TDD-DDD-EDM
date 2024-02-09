def get_postgres_uri():
    host = 'localhost'    
    port = 5432
    password = 'abc123'
    user, db_name = 'postgres', 'allocation'
    return f'postgresql://{user}:{password}@{host}:{port}/{db_name}'


def get_api_url():
    host = 'localhost'
    port = 8000
    return f"http://{host}:{port}"
    