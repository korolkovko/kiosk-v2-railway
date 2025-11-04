-- 03_payment_methods.sql
-- Insert payment methods (Level 2 - after users exist, this can be updated)
-- For now, insert without created_by

BEGIN;

INSERT INTO payment_methods (code, description_ru, description_en, is_active, created_at) VALUES
('Card', 'Карта', 'Card', true, NOW()),
('NFCDevice', 'NFC-устройство', 'NFCDevice', true, NOW()),
('QR', 'QR-код', 'QR', true, NOW())
ON CONFLICT (code) DO NOTHING;

COMMIT;

-- Show results
SELECT 'Payment methods inserted:' as info;
SELECT code, description_en, is_active FROM payment_methods ORDER BY code;