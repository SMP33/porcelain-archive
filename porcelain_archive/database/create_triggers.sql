-- Уведомление о новых задачах (LISTEN/NOTIFY)
CREATE OR REPLACE FUNCTION notify_new_task() RETURNS trigger AS $$ BEGIN PERFORM pg_notify(
        'new_task',
        json_build_object(
            'id',
            NEW.id::text,
            'type',
            NEW.type::text
        )::text
    );
RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS task_insert_notify ON task;
CREATE TRIGGER task_insert_notify
AFTER
INSERT ON task FOR EACH ROW EXECUTE FUNCTION notify_new_task();

-- Уведомление об изменениях в задачах для автообновления UI (LISTEN/NOTIFY)
CREATE OR REPLACE FUNCTION notify_task_changed() RETURNS trigger AS $$ BEGIN PERFORM pg_notify(
        'task_changed',
        NEW.id::text
    );
RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS task_change_notify ON task;
CREATE TRIGGER task_change_notify
AFTER
INSERT OR UPDATE ON task FOR EACH ROW EXECUTE FUNCTION notify_task_changed();

-- Уведомление об изменении статуса набора изменений для автообновления UI
-- (LISTEN/NOTIFY) - в том числе у других пользователей, у которых открыта
-- та же страница редактирования.
CREATE OR REPLACE FUNCTION notify_branch_changed() RETURNS trigger AS $$ BEGIN PERFORM pg_notify(
        'branch_changed',
        NEW.id::text
    );
RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS branch_status_change_notify ON branch;
CREATE TRIGGER branch_status_change_notify
AFTER
UPDATE OF status ON branch FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status) EXECUTE FUNCTION notify_branch_changed();