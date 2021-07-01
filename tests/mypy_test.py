import envium
from envium import VarGroup, var


class Environ(envium.Environ):
    class Db(VarGroup):
        name: str = var()
        user: str = var()
        password: str = var()
        host: str = var()
        port: int = var()

    class Minio(VarGroup):
        storage_endpoint: str = var()
        access_key: str = var()
        secret_key: str = var()
        media_bucket_name: str = var()

    db = Db()
    minio = Minio()
