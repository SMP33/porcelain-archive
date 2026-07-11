-- Пароль по умолчанию: admin (хеш посчитан bcrypt). Если строка уже существует
-- с пустым hash (например, из старой миграции), хеш будет проставлен задним числом.
INSERT INTO member (name, display_name, email, hash, can_create, can_review, is_admin)
VALUES ('admin', 'Administrator', NULL, '$2b$12$71UKwGlo5Wyb13g7yfIEue/tJ2R76ywV56hre.UU6jv7FM9ur4bvq', 1, 1, 1)
ON CONFLICT (name) DO UPDATE SET hash = EXCLUDED.hash WHERE member.hash IS NULL;