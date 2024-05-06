from pydantic_settings import BaseSettings, SettingsConfigDict

class PostgresSettings(BaseSettings):
    db_host: str
    db_port: int = 5432
    db_password: str
    db_user: str = 'allocation'
    db_name: str = 'allocation'

    model_config = SettingsConfigDict(extra='ignore', env_file=".env")

class ApiSettings(BaseSettings):
    api_host: str
    api_port: int = 8000

    model_config = SettingsConfigDict(extra='ignore', env_file=".env")

class RedisSettings(BaseSettings):
    redis_host: str
    redis_port: int = 6379

    model_config = SettingsConfigDict(extra='ignore', env_file=".env")

api_settings = ApiSettings()
db_settings = PostgresSettings()
redis_settings = RedisSettings()

def get_postgres_uri():
    host = db_settings.db_host    
    port = db_settings.db_port
    password = db_settings.db_password
    user, db_name = db_settings.db_user, db_settings.db_name
    return f'postgresql://{user}:{password}@{host}:{port}/{db_name}'


def get_api_url():
    host = api_settings.api_host
    port = api_settings.api_port
    return f"http://{host}:{port}"


def get_redis_host_and_port():
    host = redis_settings.redis_host
    port = redis_settings.redis_port
    return dict(host=host, port=port)
