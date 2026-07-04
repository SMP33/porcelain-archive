import psycopg2
import os
import configparser

class Database:
    """
    Класс-синглтон для управления соединением с базой данных PostgreSQL.

    Соединение устанавливается при первом создании экземпляра
    """
    _instance = None
    _connection = None

    def __new__(cls, *args, **kwargs):
        """
        Реализация паттерна Singleton.
        Создает экземпляр и соединение с БД только при первом вызове.
        """
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            
            # Получаем параметры подключения из .ini файла
            config = configparser.ConfigParser()
            config_path = f"{os.path.dirname(__file__)}/../../secret/database.ini"
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Файл конфигурации не найден: {os.path.abspath(config_path)}")
                
            config.read(config_path)
            
            # Устанавливаем соединение
            cls._connection = psycopg2.connect(
                dbname=config.get('General', 'dbname'),
                user=config.get('General', 'user'),
                password=config.get('General', 'password'),
                host=config.get('General', 'host'),
                port=config.getint('General', 'port')
            )
            
            print("Database connection established.")

            # Выполняем скрипт для создания таблиц
            sql_file_path = os.path.join(os.path.dirname(__file__), 'create_tables.sql')
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            with cls._connection.cursor() as cursor:
                cursor.execute(sql_script)
                cls._connection.commit()
            print("Database tables initialized/verified.")

        return cls._instance
    
    def init(self):
        """Инициализация."""
        return self.get_connection()

    def get_connection(self):
        """Возвращает активное соединение с базой данных."""
        return self._connection

# Создаем единственный экземпляр для импорта в других частях приложения
db = Database()
