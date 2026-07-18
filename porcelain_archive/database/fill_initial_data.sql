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