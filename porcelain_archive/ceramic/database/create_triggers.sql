-- Автоматический пересчёт search_vector документа при вставке/правке.
-- Заменяет FTS5-триггеры SQLite: вместо внешней virtual-таблицы используется
-- обычная колонка tsvector с GIN-индексом (см. create_tables.sql).

CREATE OR REPLACE FUNCTION documents_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('russian', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('russian', coalesce(NEW.author, '') || ' ' || coalesce(NEW.doc_type, '')), 'B') ||
        setweight(to_tsvector('russian', coalesce(NEW.keywords, '') || ' ' || coalesce(NEW.geography, '')), 'C') ||
        setweight(to_tsvector('russian', coalesce(NEW.description, '')), 'C') ||
        setweight(to_tsvector('russian', coalesce(NEW.full_text, '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_documents_search_vector ON documents;
CREATE TRIGGER trg_documents_search_vector
    BEFORE INSERT OR UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION documents_search_vector_update();
