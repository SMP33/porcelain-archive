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
          is_editable INTEGER DEFAULT 1, -- Доступен ли для редактирования список значений
          is_usable INTEGER DEFAULT 1, -- Может ли применяться в документах пользователем
          is_visible INTEGER DEFAULT 0, -- Виден ли обычным пользователям
          view_order INTEGER DEFAULT 0, -- Порядок отображения
          type TEXT DEFAULT 'string' -- Тип
          CHECK (type IN ('string', 'bool', 'combobox', 'multicheckbox'))
          );

-- Фактические значения указателей
CREATE    TABLE IF NOT EXISTS document_property (
          document_id BIGINT REFERENCES document (id) ON DELETE SET NULL, -- Документ
          tag TEXT REFERENCES property (tag) ON DELETE SET NULL, -- Указатель
          value TEXT, -- Значение
          UNIQUE NULLS NOT DISTINCT (document_id, tag, value)
          );

-- Переводы указателей
CREATE    TABLE IF NOT EXISTS property_translate (
          tag TEXT REFERENCES property (tag) ON DELETE CASCADE, -- Указатель
          value TEXT NOT NULL, -- Значение
          translated TEXT NOT NULL, -- Перевод
          UNIQUE (tag, value)
          );

-- Применённые патчи схемы БД (см. patch.py)
CREATE    TABLE IF NOT EXISTS patch (
          uuid UUID PRIMARY KEY UNIQUE NOT NULL -- Уникальный идентификатор патча
          );

-- ============================================================
-- Публичный сайт (ceramic): подписки.
-- Раньше жили в отдельной схеме со своим пулом соединений - объединены сюда.
-- ============================================================

-- Подписчики на новости проекта (форма в подвале сайта).
CREATE TABLE IF NOT EXISTS subscriber (
    id         BIGSERIAL PRIMARY KEY,
    email      TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Заводы как отдельная сущность удалены - объекты (фарфоровые изделия) теперь
-- document с указателем document_type = 'object' (см. porcelain_archive/ceramic/objects).
DROP TABLE IF EXISTS factory;
