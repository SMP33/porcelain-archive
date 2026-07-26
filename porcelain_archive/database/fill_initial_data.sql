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

-- Базовые указатели архива (перенесены из текущей рабочей БД). Все системные
-- (is_system=1) - принудительно видны при наличии значения и не могут быть
-- удалены. "document_type" и "page_count" дополнительно заблокированы от
-- общего редактора указателей документа (is_usable=0) - управляются только
-- программно (set_document_type, regenerate_branch_cache); значение 'object'
-- отличает документы-объекты (porcelain_archive/ceramic/objects) от обычных
-- документов архива, 'historical_document' - обычный архивный документ.
INSERT INTO property (tag, title, description, type, is_editable, is_usable, is_visible, is_system, view_order)
VALUES
    ('document_type', 'Тип документа', NULL, 'combobox', 0, 0, 0, 1, 0),
    ('document_status', 'Статус документа', NULL, 'combobox', 1, 1, 1, 1, 1),
    ('datetime', 'Полная дата издания', NULL, 'combobox', 1, 1, 0, 1, 2),
    ('year', 'Год издания', NULL, 'combobox', 1, 1, 0, 1, 3),
    ('last_change_datetime', 'Последнее изменение', 'Дата последнего изменения', 'combobox', 0, 1, 1, 1, 4),
    ('page_count', 'Число страниц', NULL, 'combobox', 0, 0, 1, 1, 5),
    ('subjects', 'Тематика', NULL, 'multicheckbox', 1, 1, 1, 0, 6),
    ('source', 'Источник', NULL, 'string', 1, 1, 0, 1, 7)
ON CONFLICT (tag) DO NOTHING;

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