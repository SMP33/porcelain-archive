-- Список пользователей
CREATE TABLE IF NOT EXISTS member (
    id BIGSERIAL PRIMARY KEY, -- Уникальный id
    name TEXT UNIQUE NOT NULL, -- Имя
    email TEXT UNIQUE, -- Почтовый адрес
    hash TEXT, -- Хеш сумма пароля
    can_create  INTEGER DEFAULT 0, -- Может ли создавать документы
    can_review  INTEGER DEFAULT 0 -- Может ли одобрять правки
);

-- Сессии пользователей
CREATE TABLE IF NOT EXISTS session (
    user_id BIGINT NOT NULL REFERENCES member(id) ON DELETE CASCADE, -- Пользователь
    id BIGSERIAL PRIMARY KEY, -- Уникальный id
    token TEXT UNIQUE NOT NULL, -- Токен сессии
    is_active INTEGER DEFAULT 1 -- Активна ли сессия
);

-- Документы
CREATE TABLE IF NOT EXISTS document (
    id BIGSERIAL PRIMARY KEY, -- Уникальный id
    name TEXT NOT NULL, -- Имя
    is_visible INTEGER DEFAULT 0 -- Виден ли обычным пользователям
);

-- Наборы изменений
CREATE TABLE IF NOT EXISTS branch (
    id BIGSERIAL PRIMARY KEY, -- Уникальный id
    author_id BIGINT NOT NULL REFERENCES member(id) ON DELETE CASCADE, -- Создатель набора изменений
    reviewer_id BIGINT NOT NULL REFERENCES member(id) ON DELETE CASCADE, -- Ревьюер
    name TEXT NOT NULL, -- Название ветки
    sha_begin TEXT, -- Коммит, с которого начинаются изменения 
    sha_merge TEXT -- Коммит, на котором произошло слияние
);

-- Начальные данные
INSERT INTO member (name, email, hash, can_create, can_review) VALUES ('admin', NULL, NULL, 1, 1) ON CONFLICT(name) DO NOTHING;