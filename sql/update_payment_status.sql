-- Update Payment table to support 'Cancelled' status
-- This migration adds the 'Cancelled' status to the paymentStatus enum

-- Note: SQLite doesn't support ALTER TYPE for enums
-- We need to recreate the constraint or handle it at the application level

-- For SQLite, we'll just document the change here
-- The application will handle the new 'Cancelled' status
-- No schema change is strictly needed as SQLite stores enums as strings

-- However, if you want to ensure data integrity, you can add a check constraint:
-- This is optional and depends on your SQLite version

-- Example check constraint (if needed):
-- ALTER TABLE payment ADD CONSTRAINT check_payment_status
-- CHECK (paymentStatus IN ('Pending', 'Paid', 'Failed', 'Cancelled'));

-- For existing databases, this migration is informational only
-- The Flask app will handle the new status value
