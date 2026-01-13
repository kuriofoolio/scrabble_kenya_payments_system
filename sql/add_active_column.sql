-- Migration: Add active column to player table
-- Purpose: Allow players to be marked as inactive after tournament registration
-- This preserves payment history while preventing duplicate registrations

-- Add active column (1 = active, 0 = inactive)
ALTER TABLE player ADD COLUMN active INTEGER DEFAULT 1;

-- Set all existing players to active
UPDATE player SET active = 1 WHERE active IS NULL;

-- Create index for faster queries on active players
CREATE INDEX IF NOT EXISTS idx_player_active ON player(active);

-- Example queries after migration:
-- Get all active players: SELECT * FROM player WHERE active = 1;
-- Get all inactive players: SELECT * FROM player WHERE active = 0;
-- Deactivate players after tournament: UPDATE player SET active = 0 WHERE playerId IN (...);
-- Reactivate players for new tournament: UPDATE player SET active = 1 WHERE playerId IN (...);
