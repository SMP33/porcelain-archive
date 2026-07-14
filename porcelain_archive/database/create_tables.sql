-- Список пользователей
CREATE    TABLE IF NOT EXISTS member (
          id BIGSERIAL PRIMARY KEY, -- Уникальный id
          name TEXT UNIQUE NOT NULL, -- Имя
          display_name TEXT, -- ФИО
          email TEXT UNIQUE, -- Почтовый адрес
          hash TEXT, -- Хеш сумма пароля
          role TEXT NOT NULL DEFAULT 'user' -- Роль
          CHECK (role IN ('user', 'moderator', 'admin'))
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
          is_visible INTEGER DEFAULT 0 -- Виден ли обычным пользователям
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
          CHECK (status IN ('in_work','in_review', 'in_accept', 'accepted', 'rejected'))
          );

-- Страницы документа
CREATE    TABLE IF NOT EXISTS page (
          commit TEXT NOT NULL, -- Коммит, к которому относится набор страниц
          pos INTEGER NOT NULL, -- Номер страницы
          image_hash TEXT, -- Хеш изображения
          text_hash TEXT, -- Хеш текстового файла
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

-- Стек редактирования
CREATE    TABLE IF NOT EXISTS branch_edit_stack (
          branch_id BIGINT REFERENCES branch (id) ON DELETE SET NULL, -- Ветка
          commit TEXT, -- Коммит
          
          data JSONB, -- Данные
          created_time TIMESTAMP, -- Время создания
          started_time TIMESTAMP, -- Время начала выполнения
          finished_time TIMESTAMP, -- Время завершения
          status TEXT NOT NULL DEFAULT 'new' -- Статус задачи
          CHECK (status IN ('new', 'queued', 'running', 'success', 'error'))
          );

-- Сообщения
CREATE    TABLE IF NOT EXISTS message (
          author_id BIGINT REFERENCES member (id) ON DELETE SET NULL, -- Автор
          receiver_type TEXT, -- Тип получателя
          receiver_id BIGSERIAL, -- ID получателя
          text TEXT -- Текст сообщения
          );