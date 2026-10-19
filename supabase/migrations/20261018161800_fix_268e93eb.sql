-- Fix mutable search_path on function _test_dynamic_exec (fix_268e93eb)
-- Incident: Function Search Path Mutable: _test_dynamic_exec

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public'
          AND p.proname = '_test_dynamic_exec'
    ) THEN
        ALTER FUNCTION public._test_dynamic_exec() SET search_path = public, pg_temp;
    END IF;
END $$;

NOTIFY pgrst, 'reload schema';
