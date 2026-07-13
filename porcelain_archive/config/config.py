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


class Config:
    common: CommonConfig
    database: DatabaseConfig
    files: FilesConfig

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


config = Config(os.environ.get('ARCHIVE_CONFIG_INI_PATH'))
