from django.db import connection

RLS_POLICY_SETUP = """
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT table_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND column_name = 'school_id'
    LOOP
        EXECUTE format(
            'ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY;',
            'public', r.table_name
        );

        -- and guard the CREATE POLICY with a existence check:
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies
            WHERE schemaname = 'public'
            AND tablename = r.table_name
            AND policyname = 'tenant_isolation_policy'
        ) THEN
            EXECUTE format(
                'CREATE POLICY tenant_isolation_policy ON %I.%I
                USING (school_id = current_setting(''app.current_school_id'')::uuid);',
                'public', r.table_name
            );
        END IF;
    END LOOP;
END $$;
"""

RLS_POLICY_TEARDOWN = """
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT table_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND column_name = 'school_id'
    LOOP
        EXECUTE format(
            'DROP POLICY IF EXISTS tenant_isolation_policy ON %I.%I;',
            'public', r.table_name
        );
        EXECUTE format(
            'ALTER TABLE %I.%I DISABLE ROW LEVEL SECURITY;',
            'public', r.table_name
        );
    END LOOP;
END $$;
"""


def enable_rls(apps, schema_editor):
    if connection.vendor != "postgresql":
        return  # no-op on SQLite (local dev) — RLS doesn't exist there
    schema_editor.execute(RLS_POLICY_SETUP)


def disable_rls(apps, schema_editor):
    if connection.vendor != "postgresql":
        return
    schema_editor.execute(RLS_POLICY_TEARDOWN)



# from django.db import migrations
# from school_core.rls import enable_rls, disable_rls


# class Migration(migrations.Migration):

#     dependencies = [
#         ("school_core", "0001_previous_migration_name"),  # ← update to your actual latest migration
#     ]

#     operations = [
#         migrations.RunPython(enable_rls, reverse_code=disable_rls),
#     ]