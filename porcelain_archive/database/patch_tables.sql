-- Патчи схемы для БД, созданных до появления соответствующих полей/ограничений
-- в create_tables.sql. Выполняется после create_tables.sql, каждый патч должен
-- быть безопасен для повторного запуска (IF NOT EXISTS / DROP ... IF EXISTS).

-- На случай существующей БД, созданной до появления этого поля.
ALTER     TABLE member
ADD       COLUMN IF NOT EXISTS created_time TIMESTAMP;

-- Статус 'to_review' ("Отправлено на проверку") между 'in_work' и 'in_review' -
-- на случай существующей БД, созданной до появления этого статуса.
ALTER     TABLE branch
DROP      CONSTRAINT IF EXISTS branch_status_check;
ALTER     TABLE branch
ADD       CONSTRAINT branch_status_check
          CHECK (status IN ('in_work', 'to_review', 'in_review', 'in_accept', 'accepted', 'rejected'));

-- property: переход с name на title, добавление is_system и view_order -
-- на случай существующей БД, созданной до появления этих полей. UNIQUE на
-- tag/title не добавляется патчем - в уже существующих данных могут быть
-- дубли, ограничение действует только для новых БД (см. create_tables.sql).
ALTER     TABLE property
ADD       COLUMN IF NOT EXISTS title TEXT;
ALTER     TABLE property
ADD       COLUMN IF NOT EXISTS is_system INTEGER DEFAULT 0;
ALTER     TABLE property
ADD       COLUMN IF NOT EXISTS view_order INTEGER DEFAULT 0;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'property' AND column_name = 'name'
    ) THEN
        UPDATE property SET title = name WHERE title IS NULL;
    END IF;
END $$;

-- property_enum: собственный id (раньше строки без id) и is_pointer -
-- на случай существующей БД, созданной до появления этих полей.
ALTER     TABLE property_enum
ADD       COLUMN IF NOT EXISTS id BIGSERIAL;
ALTER     TABLE property_enum
ADD       COLUMN IF NOT EXISTS is_pointer INTEGER DEFAULT 1;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conrelid = 'property_enum'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE property_enum ADD PRIMARY KEY (id);
    END IF;
END $$;

-- document_property: переход с (property_id, value) на ссылку property_enum_id -
-- на случай существующей БД, созданной до этого изменения. Перенос данных
-- best-effort - строки, для которых не нашлось соответствия в property_enum
-- (например, если value уже был переименован), останутся с property_enum_id = NULL.
ALTER     TABLE document_property
ADD       COLUMN IF NOT EXISTS property_enum_id BIGINT REFERENCES property_enum (id) ON DELETE SET NULL;

-- document.deleted: на случай существующей БД, созданной до появления этого поля.
ALTER     TABLE document
ADD       COLUMN IF NOT EXISTS deleted INTEGER DEFAULT 0;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'document_property' AND column_name = 'property_id'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'document_property' AND column_name = 'value'
    ) THEN
        UPDATE document_property dp
        SET property_enum_id = pe.id
        FROM property_enum pe
        WHERE dp.property_enum_id IS NULL
          AND dp.property_id = pe.property_id
          AND dp.value = pe.value;

        ALTER TABLE document_property DROP COLUMN IF EXISTS property_id;
        ALTER TABLE document_property DROP COLUMN IF EXISTS value;
    END IF;
END $$;
