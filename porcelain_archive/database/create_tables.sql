-- Список пользователей
CREATE    TABLE IF NOT EXISTS member (
          id BIGSERIAL PRIMARY KEY, -- Уникальный id
          name TEXT UNIQUE NOT NULL, -- Имя
          display_name TEXT, -- ФИО
          email TEXT UNIQUE, -- Почтовый адрес
          hash TEXT, -- Хеш сумма пароля
          role TEXT NOT NULL DEFAULT 'user' -- Роль
          CHECK (role IN ('user', 'moderator', 'admin')),
          created_time TIMESTAMP -- Время создания учётной записи
          );

-- Сессии пользователей
CREATE    TABLE IF NOT EXISTS session (
          user_id BIGINT NOT NULL REFERENCES member (id) ON DELETE CASCADE, -- Пользователь
          id BIGSERIAL PRIMARY KEY, -- Уникальный id
          token TEXT UNIQUE NOT NULL, -- Токен сессии
          is_active INTEGER DEFAULT 1 -- Активна ли сессия
          );

-- Документы
CREATE    TABLE IF NOT EXISTS document (
          id BIGSERIAL PRIMARY KEY, -- Уникальный id
          name TEXT NOT NULL, -- Имя
          meta JSONB, -- Мета информация о документе: теги, авторы, дата выхода...
          is_visible INTEGER DEFAULT 0, -- Виден ли обычным пользователям
          deleted INTEGER DEFAULT 0 -- Удалён
          );

-- Версия документа
CREATE    TABLE IF NOT EXISTS branch (
          id BIGSERIAL PRIMARY KEY, -- Уникальный id
          document_id BIGINT NOT NULL REFERENCES document (id) ON DELETE CASCADE, -- Документ
          author_id BIGINT REFERENCES member (id) ON DELETE SET NULL, -- Создатель набора изменений
          reviewer_id BIGINT REFERENCES member (id) ON DELETE SET NULL, -- Ревьюер
          name TEXT DEFAULT NULL, -- Название ветки
          meta JSONB, -- Мета информация о версии документа
          created_time TIMESTAMP, -- Время создания
          last_change_time TIMESTAMP, -- Время последнего изменения
          initial_commit TEXT, -- Коммит на момент создания ветки
          last_commit TEXT, -- Коммит последнего обновления кеша страниц
          status TEXT NOT NULL DEFAULT 'in_work' -- Статус набора изменений
          CHECK (
          status IN ('in_work', 'to_review', 'in_review', 'in_accept', 'accepted', 'rejected')
          )
          );

-- Страницы документа
CREATE    TABLE IF NOT EXISTS page (
          commit TEXT NOT NULL, -- Коммит, к которому относится набор страниц
          pos INTEGER NOT NULL, -- Номер страницы
          image_hash TEXT, -- Хеш изображения
          text_hash TEXT, -- Хеш текстового файла
          image_file TEXT, -- Файл изображения
          text_file TEXT, -- Текстовый файл
          PRIMARY KEY (commit, pos)
          );

-- Задачи
CREATE    TABLE IF NOT EXISTS task (
          id BIGSERIAL PRIMARY KEY, -- Уникальный id
          author_id BIGINT REFERENCES member (id) ON DELETE SET NULL, -- Автор
          type TEXT NOT NULL, -- Тип
          data JSONB, -- Данные
          created_time TIMESTAMP, -- Время создания
          started_time TIMESTAMP, -- Время начала выполнения
          finished_time TIMESTAMP, -- Время завершения
          status TEXT NOT NULL DEFAULT 'new' -- Статус задачи
          CHECK (status IN ('new', 'queued', 'running', 'success', 'error'))
          );

-- Сообщения
CREATE    TABLE IF NOT EXISTS message (
          id BIGSERIAL PRIMARY KEY, -- Уникальный id
          author_id BIGINT REFERENCES member (id) ON DELETE SET NULL, -- Автор (NULL - аноним)
          receiver_type TEXT, -- Тип получателя
          receiver_id BIGSERIAL, -- ID получателя
          TEXT TEXT, -- Текст сообщения
          is_read INTEGER DEFAULT 0, -- Прочитано ли сообщение
          create_time TIMESTAMP -- Время создания
          );

-- Отметка "важное" для сообщений (например, обратной связи - message.receiver_type = 'feedback').
-- Присутствие строки = отмечено важным.
CREATE    TABLE IF NOT EXISTS important_feedback (
          message_id BIGINT PRIMARY KEY REFERENCES message (id) ON DELETE CASCADE -- Сообщение
          );

-- Указатели
CREATE    TABLE IF NOT EXISTS property (
          id BIGSERIAL PRIMARY KEY, -- Уникальный id
          tag TEXT NOT NULL UNIQUE, -- Имя
          title TEXT NOT NULL UNIQUE, -- Отображаемое имя
          description TEXT, -- Описание
          is_list INTEGER DEFAULT 0, -- Список или одно значение
          is_editable INTEGER DEFAULT 1, -- Доступно ли для редактирования
          is_visible INTEGER DEFAULT 0, -- Виден ли обычным пользователям
          is_system INTEGER DEFAULT 0, -- Системный параметр
          view_order INTEGER DEFAULT 0 -- Порядок отображения
          );

-- Доступные значения указателей
CREATE    TABLE IF NOT EXISTS property_enum (
          id BIGSERIAL PRIMARY KEY, -- Уникальный id
          property_id BIGINT REFERENCES property (id) ON DELETE SET NULL, -- Указатель
          value TEXT, -- Значение
          is_pointer INTEGER DEFAULT 1 -- Считается ли значение указателем
          );

-- Фактические значения указателей
CREATE    TABLE IF NOT EXISTS document_property (
          document_id BIGINT REFERENCES document (id) ON DELETE SET NULL, -- Документ
          property_enum_id BIGINT REFERENCES property_enum (id) ON DELETE SET NULL -- Значение указателя
          );

-- Указатели документа читаются по документу (карточка) и по значению (фасеты, фильтр)
CREATE    INDEX IF NOT EXISTS document_property_document_idx ON document_property (document_id);
CREATE    INDEX IF NOT EXISTS document_property_enum_idx ON document_property (property_enum_id);

-- ============================================================
-- Публичный сайт (ceramic): подписки и объекты (фарфоровые изделия).
-- Раньше жили в отдельной схеме со своим пулом соединений - объединены сюда.
-- Порядок важен: object_property ссылается на property_enum выше.
-- ============================================================

-- Подписчики на новости проекта (форма в подвале сайта).
CREATE TABLE IF NOT EXISTS subscriber (
    id         BIGSERIAL PRIMARY KEY,
    email      TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Заводы как отдельная сущность удалены - см. porcelain_object ниже.
DROP TABLE IF EXISTS factory;

-- Объекты (отдельные фарфоровые изделия): название, описание, фото.
-- Без привязки к документам и без атрибутов завода-изготовителя.
CREATE TABLE IF NOT EXISTS porcelain_object (
    id         BIGSERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    notes      TEXT,        -- описание
    cover_key  TEXT,        -- ключ фото в ceramic-хранилище
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Видимость объекта для посетителей сайта (0 - скрыт, виден только в админке).
ALTER TABLE porcelain_object ADD COLUMN IF NOT EXISTS is_visible INTEGER DEFAULT 1;

-- Фотографии объекта (галерея). Первая по sort_order - обложка.
CREATE TABLE IF NOT EXISTS object_image (
    id         BIGSERIAL PRIMARY KEY,
    object_id  BIGINT NOT NULL REFERENCES porcelain_object (id) ON DELETE CASCADE,
    image_key  TEXT NOT NULL,  -- ключ файла в ceramic-хранилище
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS object_image_object_idx ON object_image (object_id, sort_order);

-- Перенос одиночной обложки в галерею и отказ от porcelain_object.cover_key.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'porcelain_object' AND column_name = 'cover_key'
    ) THEN
        INSERT INTO object_image (object_id, image_key, sort_order)
        SELECT id, cover_key, 0 FROM porcelain_object
        WHERE cover_key IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM object_image oi WHERE oi.object_id = porcelain_object.id);
        ALTER TABLE porcelain_object DROP COLUMN cover_key;
    END IF;
END $$;

-- Указатели объекта (значения property_enum, общие с документами).
CREATE TABLE IF NOT EXISTS object_property (
    object_id        BIGINT NOT NULL REFERENCES porcelain_object (id) ON DELETE CASCADE,
    property_enum_id BIGINT NOT NULL REFERENCES property_enum (id) ON DELETE CASCADE,
    PRIMARY KEY (object_id, property_enum_id)
);
