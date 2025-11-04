-- 04_branches.sql
-- Insert branches (simplified - no user dependencies)

BEGIN;

INSERT INTO branches (name, address, work_hours, legal_entity, created_at) 
VALUES (
    'ZeroPoint',
    '{"street":"Malyisheva","city":"Ekaterinburg","zip":"620000"}'::jsonb,
    '{"mon-sun":"08:00-24:00"}'::jsonb,
    '{"tax_id":"RU123456789","name":"ZeroCulture"}'::jsonb,
    NOW()
)
ON CONFLICT (name) DO NOTHING;

COMMIT;

-- Show results
SELECT 'Branches inserted:' as info;
SELECT name, created_at FROM branches;