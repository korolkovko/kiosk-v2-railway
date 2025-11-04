-- Seed data for promoted_label table
-- This configures the promoted items category display labels

-- Insert default promoted label configuration
INSERT INTO promoted_label (name, ru_label, en_label)
VALUES ('promoted', 'НОВИНКИ!', 'NEW!')
ON CONFLICT (name) DO UPDATE
SET
    ru_label = EXCLUDED.ru_label,
    en_label = EXCLUDED.en_label;

-- Note: The 'name' field is used for media filenames on S3/local storage
-- For example, if name='promoted', the system will look for:
--   - S3/Local: categories_promoted/promoted.mp4 or promoted.png
--
-- The ru_label and en_label are what users see in the UI
