-- 01_roles.sql
-- Insert default roles (Level 1 - No dependencies)

BEGIN;

INSERT INTO roles (name, permissions, created_at) VALUES
('superadmin', NULL, NOW()),
('admin', NULL, NOW()),
('customer', NULL, NOW()),
('kiosk', NULL, NOW()),
('externalKitchen', NULL, NOW()),
('externalPostBox', NULL, NOW())
ON CONFLICT (name) DO NOTHING;

COMMIT;

-- Show results
SELECT 'Roles inserted:' as info;
SELECT name FROM roles ORDER BY name;