import configparser
import os


class CommonConfig:
    root: str


class DatabaseConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str


class FilesConfig:
    repos_root: str
    repos_branch_root: str
    cache_path: str
    log_path: str
    ceramic_storage_backend: str
    ceramic_local_root: str


class Ceramics3Config:
    endpoint_url: str
    access_key_id: str
    secret_access_key: str
    bucket_name: str
    public_base_url: str


class CeramicsiteConfig:
    app_env: str
    secret_key: str
    admin_password: str


class Config:
    common: CommonConfig
    database: DatabaseConfig
    files: FilesConfig
    ceramics3: Ceramics3Config
    ceramicsite: CeramicsiteConfig

    def __init__(self, path: str):
        parser = configparser.ConfigParser()
        if not path or not parser.read(path):
            raise FileNotFoundError(f"Файл конфигурации не найден: {path}")

        self.common = CommonConfig()
        self.common.root = parser.get('Common', 'root')

        self.database = DatabaseConfig()
        self.database.host = parser.get('Database', 'host')
        self.database.port = parser.getint('Database', 'port')
        self.database.dbname = parser.get('Database', 'dbname')
        self.database.user = parser.get('Database', 'user')
        self.database.password = parser.get('Database', 'password')

        self.files = FilesConfig()
        self.files.repos_root = parser.get('Files', 'repos_root')
        self.files.repos_branch_root = parser.get('Files', 'repos_branch_root')
        self.files.cache_path = parser.get('Files', 'cache_path')
        self.files.log_path = parser.get('Files', 'log_path')
        self.files.ceramic_storage_backend = parser.get('Files', 'ceramic_storage_backend')
        self.files.ceramic_local_root = parser.get('Files', 'ceramic_local_root')

        self.ceramics3 = Ceramics3Config()
        self.ceramics3.endpoint_url = parser.get('CeramicS3', 'endpoint_url')
        self.ceramics3.access_key_id = parser.get('CeramicS3', 'access_key_id')
        self.ceramics3.secret_access_key = parser.get('CeramicS3', 'secret_access_key')
        self.ceramics3.bucket_name = parser.get('CeramicS3', 'bucket_name')
        self.ceramics3.public_base_url = parser.get('CeramicS3', 'public_base_url')

        self.ceramicsite = CeramicsiteConfig()
        self.ceramicsite.app_env = parser.get('CeramicSite', 'app_env')
        self.ceramicsite.secret_key = parser.get('CeramicSite', 'secret_key')
        self.ceramicsite.admin_password = parser.get('CeramicSite', 'admin_password')


config = Config(os.environ.get('ARCHIVE_CONFIG_INI_PATH'))
