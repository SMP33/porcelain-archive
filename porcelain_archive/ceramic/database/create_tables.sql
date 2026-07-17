-- Схема архива: заводы, документы, страницы, пользователи/сессии, обратная связь.

CREATE TABLE IF NOT EXISTS factories (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    location    TEXT,
    founded     INTEGER,           -- год основания
    closed      INTEGER,           -- год закрытия (NULL = работает)
    notes       TEXT,
    image_key   TEXT,              -- ключ обложки в хранилище
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS documents (
    id             SERIAL PRIMARY KEY,
    factory_id     INTEGER REFERENCES factories(id) ON DELETE SET NULL,
    title          TEXT NOT NULL,
    doc_type       TEXT,           -- приказ, патент, переписка, тех.условия, …
    doc_date       TEXT,           -- ISO дата или произвольная строка
    description    TEXT,
    author         TEXT,
    source_archive TEXT,           -- название архива
    fund           TEXT,           -- фонд (ф.)
    inventory_no   TEXT,           -- опись (оп.)
    case_no        TEXT,           -- дело (д.)
    sheets         TEXT,           -- листы (лл. 1-15)
    authenticity   TEXT,           -- Подлинник / Копия / Заверенная копия / Фотокопия
    language       TEXT,           -- язык документа
    keywords       TEXT,           -- ключевые слова через запятую
    geography      TEXT,           -- географическая принадлежность
    full_text      TEXT,           -- склейка ocr_text страниц по порядку
    year           INTEGER,        -- нормализованный год из doc_date
    page_count     INTEGER NOT NULL DEFAULT 0,
    search_vector  tsvector,       -- полнотекстовый индекс, обновляется триггером
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_documents_factory ON documents(factory_id);
CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_year ON documents(year);
CREATE INDEX IF NOT EXISTS idx_documents_search_vector ON documents USING GIN(search_vector);

CREATE TABLE IF NOT EXISTS pages (
    id           SERIAL PRIMARY KEY,
    document_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number  INTEGER NOT NULL,
    storage_key  TEXT NOT NULL,    -- ключ оригинала в хранилище
    thumb_key    TEXT NOT NULL,    -- ключ превью в хранилище
    ocr_text     TEXT,             -- распознанный/вычитанный текст этой страницы
    UNIQUE(document_id, page_number)
);

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'contributor' CHECK (role IN ('admin', 'contributor')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Сессии входа: cookie session_token хранит только token, роль/логин читаются из БД.
CREATE TABLE IF NOT EXISTS sessions (
    token      TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_active  BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

CREATE TABLE IF NOT EXISTS feedback (
    id           SERIAL PRIMARY KEY,
    name         TEXT,
    email        TEXT,
    message      TEXT NOT NULL,
    is_read      BOOLEAN NOT NULL DEFAULT false,
    is_important BOOLEAN NOT NULL DEFAULT false,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS subscribers (
    id         SERIAL PRIMARY KEY,
    email      TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_subscribers_email ON subscribers (lower(email));
