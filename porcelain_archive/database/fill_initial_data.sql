-- По одному пользователю на каждую роль, логин/пароль/display_name совпадают
-- с названием роли (хеши паролей посчитаны bcrypt). Если строка уже существует
-- с пустым hash (например, из старой миграции), хеш будет проставлен задним числом.
INSERT INTO member (name, display_name, email, hash, role)
VALUES ('user', 'Пользователь', NULL, '$2b$12$JFEBG8IAN5OGlis65n/Rre9vKt0aN9NM4EQbCp8ZMMaqHrpE3IH2a', 'user')
ON CONFLICT (name) DO NOTHING;

INSERT INTO member (name, display_name, email, hash, role)
VALUES ('moderator', 'Модератор', NULL, '$2b$12$hCXtCtl626P2Lt5lijMnyuk4igEm40xSjYU7GBo71eSnNPRRmnWie', 'moderator')
ON CONFLICT (name) DO NOTHING;

INSERT INTO member (name, display_name, email, hash, role)
VALUES ('admin', 'Администратор', NULL, '$2b$12$71UKwGlo5Wyb13g7yfIEue/tJ2R76ywV56hre.UU6jv7FM9ur4bvq', 'admin')
ON CONFLICT (name) DO NOTHING;

INSERT INTO member (name, display_name, email, hash, role)
VALUES ('admin', 'Администратор', NULL, '$2b$12$71UKwGlo5Wyb13g7yfIEue/tJ2R76ywV56hre.UU6jv7FM9ur4bvq', 'admin')
ON CONFLICT (name) DO NOTHING;

-- Указатели (property) создаются и синхронизируются в Database.fill_initial_property
-- (вызывается до этого файла). Здесь - только пул допустимых значений и переводы.
-- Значение 'object' отличает документы-объекты (porcelain_archive/ceramic/objects)
-- от обычных документов архива, 'historical_document' - обычный архивный документ.
INSERT INTO document_property (document_id, tag, value)
VALUES
    (NULL, 'document_type', 'object'),
    (NULL, 'document_type', 'historical_document'),
    (NULL, 'document_status', 'in_work'),
    (NULL, 'document_status', 'need_help'),
    (NULL, 'document_status', 'finished')
ON CONFLICT (document_id, tag, value) DO NOTHING;

INSERT INTO property_translate (tag, value, translated)
VALUES
    ('document_type', 'object', 'Объект'),
    ('document_type', 'historical_document', 'Исторический документ'),
    ('document_status', 'in_work', 'В работе'),
    ('document_status', 'need_help', 'Нужны правки'),
    ('document_status', 'finished', 'Закончен')
ON CONFLICT (tag, value) DO NOTHING;