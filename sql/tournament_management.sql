-- Tournament Management SQL Scripts
-- Use these scripts to manage player active status between tournaments

-- ============================================================================
-- AFTER TOURNAMENT ENDS: Deactivate all registered players
-- ============================================================================
-- This preserves all payment history while preparing for the next tournament
-- Run this after a tournament concludes

UPDATE player
SET active = 0
WHERE playerId IN (
    SELECT DISTINCT playerId FROM ticket
);

-- Verify deactivation
SELECT
    COUNT(*) as inactive_players,
    (SELECT COUNT(*) FROM player WHERE active = 1) as active_players,
    (SELECT COUNT(*) FROM player) as total_players
FROM player WHERE active = 0;


-- ============================================================================
-- BEFORE NEW TOURNAMENT: Activate all players
-- ============================================================================
-- Makes all players available for registration in the new tournament
-- Run this before opening registration for a new tournament

UPDATE player SET active = 1;

-- Verify activation
SELECT
    COUNT(*) as active_players,
    (SELECT COUNT(*) FROM player WHERE active = 0) as inactive_players,
    (SELECT COUNT(*) FROM player) as total_players
FROM player WHERE active = 1;


-- ============================================================================
-- OPTIONAL: Clear tickets before new tournament (use with caution!)
-- ============================================================================
-- WARNING: This deletes ticket records. Only use if you want to completely
-- clear registrations for a fresh start. Payment history is preserved.

-- First, backup tickets
-- CREATE TABLE ticket_backup_[date] AS SELECT * FROM ticket;

-- Then delete tickets (this will allow previously registered players to register again)
-- DELETE FROM ticket;


-- ============================================================================
-- QUERY: View active vs inactive players
-- ============================================================================
SELECT
    active,
    COUNT(*) as count,
    CASE
        WHEN active = 1 THEN 'Active (available for registration)'
        WHEN active = 0 THEN 'Inactive (registered in previous tournament)'
        ELSE 'Unknown status'
    END as status_description
FROM player
GROUP BY active;


-- ============================================================================
-- QUERY: View registered players for current tournament
-- ============================================================================
SELECT
    p.playerName,
    p.playerRating,
    p.playerEmail,
    p.paidUp,
    p.active,
    d.title as division,
    t.ticketPrice,
    pay.paymentStatus,
    pay.dateCreated as registered_date
FROM player p
INNER JOIN ticket t ON p.playerId = t.playerId
INNER JOIN division d ON t.divisionId = d.divisionId
INNER JOIN payment pay ON t.paymentId = pay.paymentId
WHERE pay.paymentStatus = 'Paid'
ORDER BY pay.dateCreated DESC;


-- ============================================================================
-- QUERY: Find players who registered but payment failed
-- ============================================================================
SELECT
    p.playerName,
    p.playerRating,
    p.active,
    pay.paymentStatus,
    pay.phoneNumber,
    pay.dateCreated
FROM player p
INNER JOIN ticket t ON p.playerId = t.playerId
INNER JOIN payment pay ON t.paymentId = pay.paymentId
WHERE pay.paymentStatus IN ('Failed', 'Cancelled', 'Pending')
ORDER BY pay.dateCreated DESC;


-- ============================================================================
-- QUERY: Tournament statistics
-- ============================================================================
SELECT
    'Total Players' as metric,
    COUNT(*) as count
FROM player
UNION ALL
SELECT
    'Active Players',
    COUNT(*)
FROM player WHERE active = 1
UNION ALL
SELECT
    'Inactive Players',
    COUNT(*)
FROM player WHERE active = 0
UNION ALL
SELECT
    'Registered Players (Current)',
    COUNT(DISTINCT t.playerId)
FROM ticket t
INNER JOIN payment pay ON t.paymentId = pay.paymentId
WHERE pay.paymentStatus = 'Paid'
UNION ALL
SELECT
    'Total Revenue (Current Tournament)',
    CAST(SUM(pay.totalAmount) as INTEGER)
FROM payment pay
WHERE pay.paymentStatus = 'Paid';


-- ============================================================================
-- EMERGENCY: Reactivate specific players by name
-- ============================================================================
-- Use if you accidentally deactivated someone who should be available
-- UPDATE player
-- SET active = 1
-- WHERE playerName IN ('PLAYER NAME 1', 'PLAYER NAME 2');


-- ============================================================================
-- EMERGENCY: Deactivate specific players by ID
-- ============================================================================
-- Use if you need to manually deactivate specific players
-- UPDATE player
-- SET active = 0
-- WHERE playerId IN (1, 2, 3, 4, 5);
