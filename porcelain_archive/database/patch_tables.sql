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
