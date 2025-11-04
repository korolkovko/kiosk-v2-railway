-- 02_basic_lookups.sql
-- Insert basic lookup data that doesn't require users (Level 2)
-- Note: These will not have created_by initially - can be updated later

BEGIN;

-- Units of Measure (without created_by for now)
INSERT INTO units_of_measure (name_eng, created_at) VALUES
('piece', NOW())
ON CONFLICT (name_eng) DO NOTHING;


COMMIT;

-- Show results
SELECT 'Basic lookup data inserted:' as info;
SELECT 'Units:' as type, COUNT(*) as count FROM units_of_measure
UNION ALL
SELECT 'Food Categories:', COUNT(*) FROM food_categories;