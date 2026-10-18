-- Fix mutable search_path on function _test_migration_func (fix_c3b85768)
-- Incident: Function Search Path Mutable: _test_migration_func

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public'
          AND p.proname = '_test_migration_func'
    ) THEN
        ALTER FUNCTION public._test_migration_func() SET search_path = public, pg_temp;
    END IF;
END $$;

NOTIFY pgrst, 'reload schema';
