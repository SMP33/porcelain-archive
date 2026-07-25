-- Схема ceramic.
-- Пользователи/сессии - общие с porcelain_archive, см. member/session.
-- Документы/страницы - тоже общие с porcelain_archive (document/branch/page).
-- Обратная связь - тоже общая с porcelain_archive (message/important_feedback).

-- Подписчики на новости проекта (форма в подвале сайта).
CREATE TABLE IF NOT EXISTS subscriber (
    id         BIGSERIAL PRIMARY KEY,
    email      TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Объекты (заводы/предприятия). Документы привязываются через document.meta->>'factory_id'.
CREATE TABLE IF NOT EXISTS factory (
    id         BIGSERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    location   TEXT,        -- местонахождение
    founded    INTEGER,     -- год основания
    closed     INTEGER,     -- год закрытия (NULL = работает)
    notes      TEXT,        -- описание
    cover_key  TEXT,        -- ключ обложки в ceramic-хранилище
    created_at TIMESTAMPTZ DEFAULT now()
);
