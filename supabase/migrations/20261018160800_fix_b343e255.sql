-- Fix mutable search_path on function _test_dynamic_sql (fix_b343e255)
-- Incident: Function Search Path Mutable: _test_dynamic_sql

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public'
          AND p.proname = '_test_dynamic_sql'
    ) THEN
        ALTER FUNCTION public._test_dynamic_sql() SET search_path = public, pg_temp;
    END IF;
END $$;

NOTIFY pgrst, 'reload schema';
