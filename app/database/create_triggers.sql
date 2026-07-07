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