import envium
from envium import EnvGroup, env_var


class Environ(envium.Environ):
    class Db(EnvGroup):
        name: str = env_var()
        user: str = env_var()
        password: str = env_var()
        host: str = env_var()
        port: int = env_var()

    class Minio(EnvGroup):
        storage_endpoint: str = env_var()
        access_key: str = env_var()
        secret_key: str = env_var()
        media_bucket_name: str = env_var()

    db = Db()
    minio = Minio()
