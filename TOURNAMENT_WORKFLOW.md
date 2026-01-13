# Tournament Workflow Guide

This guide explains how to manage player registrations across multiple tournaments using the active/inactive player system.

## Overview

Instead of deleting player and payment data between tournaments, the system uses an **active status** to control which players can register. This approach:

- ✅ **Preserves payment history** - All payment records remain intact
- ✅ **Prevents duplicate registrations** - Players who registered for the previous tournament are marked inactive
- ✅ **Maintains data integrity** - Foreign key relationships stay valid
- ✅ **Enables reporting** - Historical data available for analysis
- ✅ **Simplifies reactivation** - Easy to make players available again

---

## Player States

| State | Active Value | Can Register? | Has Ticket? | Description |
|-------|-------------|---------------|-------------|-------------|
| **New** | 1 | ✅ Yes | ❌ No | New player, never registered |
| **Available** | 1 | ✅ Yes | ❌ No | Player from previous tournament, reactivated |
| **Registered** | 0 | ❌ No | ✅ Yes | Player registered for previous tournament |

---

## Workflow Between Tournaments

### **Phase 1: Tournament is Active**
Players register and pay for the current tournament. System functions normally.

```
Active Players (1500) → Can Register → Create Tickets → Payment
```

### **Phase 2: Tournament Ends**
After the tournament concludes, mark all registered players as inactive.

**Option A: Use API Endpoint (Recommended)**
```bash
curl -X POST http://localhost:5001/api/players/deactivate-registered
```

**Option B: Use SQL Script**
```bash
sqlite3 instance/sk_tickets.db < sql/tournament_management.sql
# Run the "AFTER TOURNAMENT ENDS" section
```

**Result:**
- Players with tickets → `active = 0` (inactive)
- Players without tickets → `active = 1` (still active)
- All payment and ticket data → **preserved**

### **Phase 3: Prepare for Next Tournament**
Before opening registration for the next tournament, you have two options:

#### **Option 1: Keep Previous Tournament Data (Recommended)**
Activate all players while keeping tickets:

```bash
# Via API
curl -X POST http://localhost:5001/api/players/activate-all

# Via SQL
sqlite3 instance/sk_tickets.db "UPDATE player SET active = 1;"
```

**Result:**
- All players → `active = 1`
- Previous tickets → **still exist**
- System behavior: Players with existing tickets from the previous tournament will see "already registered" error if they try to register again

**Important:** This means players who registered for the previous tournament CANNOT register for the new one unless you also clear tickets.

#### **Option 2: Fresh Start (Clear Previous Registrations)**
Activate all players AND clear tickets:

```bash
# Backup first!
sqlite3 instance/sk_tickets.db "backups/.backup backup_$(date +%Y%m%d).db"

# Clear tickets
sqlite3 instance/sk_tickets.db "DELETE FROM ticket;"

# Activate all players
sqlite3 instance/sk_tickets.db "UPDATE player SET active = 1;"
```

**Result:**
- All players → `active = 1`
- Previous tickets → **deleted**
- Previous payments → **preserved** (for accounting)
- All players can register for the new tournament

---

## API Endpoints for Tournament Management

### 1. Deactivate Registered Players
Marks all players who have tickets as inactive.

```bash
POST /api/players/deactivate-registered
```

**Response:**
```json
{
  "message": "Successfully deactivated 250 registered players",
  "count": 250,
  "playerIds": [1, 2, 3, ...]
}
```

### 2. Activate All Players
Makes all players available for registration.

```bash
POST /api/players/activate-all
```

**Response:**
```json
{
  "message": "Successfully activated 250 players",
  "count": 250
}
```

### 3. Toggle Specific Players
Manually activate or deactivate specific players.

```bash
POST /api/players/toggle-active
Content-Type: application/json

{
  "playerIds": [1, 2, 3, 4, 5],
  "active": 1
}
```

**Response:**
```json
{
  "message": "Successfully activated 5 players",
  "count": 5
}
```

---

## Recommended Workflows

### **Workflow A: Preserve Tournament Data (Best for Accounting)**

Use this if you want to keep complete records of each tournament separately.

1. **After Tournament:** Deactivate registered players
   ```bash
   curl -X POST http://localhost:5001/api/players/deactivate-registered
   ```

2. **Before Next Tournament:** Create new ticket records (keep old ones)
   - Update tournament details (date, venue, etc.)
   - Activate all players
   ```bash
   curl -X POST http://localhost:5001/api/players/activate-all
   ```

3. **Constraint:** Players with existing tickets CANNOT register again

**Pros:**
- Complete historical records
- Each tournament's data is separate
- Easy to generate per-tournament reports

**Cons:**
- Players who registered before cannot register again (unless you manually delete their tickets)

---

### **Workflow B: Reuse Player Pool (Best for Ongoing Tournaments)**

Use this if players should be able to register for every tournament.

1. **After Tournament:** Clear tickets, deactivate all
   ```bash
   # Backup database
   sqlite3 instance/sk_tickets.db "backups/.backup backup_$(date +%Y%m%d).db"

   # Clear tickets
   sqlite3 instance/sk_tickets.db "DELETE FROM ticket;"
   ```

2. **Before Next Tournament:** Activate all players
   ```bash
   curl -X POST http://localhost:5001/api/players/activate-all
   ```

**Pros:**
- Players can register for multiple tournaments
- Clean slate for each tournament
- Simple management

**Cons:**
- Lose per-tournament ticket records
- Payment records show transactions but not which tournament

---

## SQL Queries for Management

### Check Player Status Distribution
```sql
SELECT
    active,
    COUNT(*) as count,
    CASE
        WHEN active = 1 THEN 'Active'
        WHEN active = 0 THEN 'Inactive'
    END as status
FROM player
GROUP BY active;
```

### View Registered Players for Current Tournament
```sql
SELECT
    p.playerName,
    d.title as division,
    t.ticketPrice,
    pay.paymentStatus,
    pay.dateCreated
FROM player p
INNER JOIN ticket t ON p.playerId = t.playerId
INNER JOIN division d ON t.divisionId = d.divisionId
INNER JOIN payment pay ON t.paymentId = pay.paymentId
WHERE pay.paymentStatus = 'Paid'
ORDER BY pay.dateCreated DESC;
```

### Calculate Tournament Revenue
```sql
SELECT
    SUM(totalAmount) as total_revenue,
    COUNT(*) as successful_payments
FROM payment
WHERE paymentStatus = 'Paid';
```

---

## Database Schema

### Player Table
```sql
CREATE TABLE player (
    playerId INTEGER PRIMARY KEY,
    playerName VARCHAR(255) NOT NULL,
    playerRating INTEGER NOT NULL,
    playerEmail VARCHAR(255),
    paidUp INTEGER DEFAULT 0,  -- Membership fee status
    active INTEGER DEFAULT 1    -- Availability for registration
);
```

### Index
```sql
CREATE INDEX idx_player_active ON player(active);
```

---

## Troubleshooting

### "Player already registered" error for new tournament

**Cause:** Player has a ticket from the previous tournament.

**Solution:**
```sql
-- Option 1: Clear all tickets
DELETE FROM ticket;

-- Option 2: Clear specific player's tickets
DELETE FROM ticket WHERE playerId IN (1, 2, 3);
```

### Player not showing up in registration list

**Possible causes:**
1. Player is inactive (`active = 0`)
2. Player already has a ticket

**Check status:**
```sql
SELECT playerId, playerName, active,
       (SELECT COUNT(*) FROM ticket WHERE ticket.playerId = player.playerId) as has_ticket
FROM player
WHERE playerName LIKE '%PLAYER NAME%';
```

**Solution:**
```sql
-- Activate the player
UPDATE player SET active = 1 WHERE playerId = X;

-- Delete their old ticket if needed
DELETE FROM ticket WHERE playerId = X;
```

---

## Best Practices

1. **Always backup before bulk operations**
   ```bash
   sqlite3 instance/sk_tickets.db "backups/.backup backup_$(date +%Y%m%d_%H%M%S).db"
   ```

2. **Test on a copy first**
   ```bash
   cp instance/sk_tickets.db instance/sk_tickets_test.db
   # Run operations on test database
   ```

3. **Document tournament dates**
   - Keep a log of when you deactivate/activate players
   - Note which backup corresponds to which tournament

4. **Verify after bulk operations**
   ```sql
   -- Check counts
   SELECT active, COUNT(*) FROM player GROUP BY active;

   -- Check tickets
   SELECT COUNT(*) FROM ticket;
   ```

5. **Use API endpoints for automation**
   - Create a script to run after each tournament
   - Schedule activation before next tournament opens

---

## Example: Complete Tournament Cycle

```bash
# === TOURNAMENT 1: Nairobi (February 2025) ===

# 1. Tournament is live, players register (automatic)
# 2. Tournament ends February 8, 2025

# 3. Deactivate registered players
curl -X POST http://localhost:5000/api/players/deactivate-registered

# 4. Backup database
sqlite3 instance/sk_tickets.db "backups/.backup backups/nairobi_feb2025.db"


# === PREPARE FOR TOURNAMENT 2: Kitui (March 2025) ===

# 5. Clear tickets for fresh registrations
sqlite3 instance/sk_tickets.db "DELETE FROM ticket;"

# 6. Activate all players
curl -X POST http://localhost:5000/api/players/activate-all

# 7. Update tournament details in index.html
# 8. Open registration for Kitui tournament
```

---

## Support

For questions or issues, check:
- [sql/tournament_management.sql](sql/tournament_management.sql) - Ready-to-use SQL queries
- [sql/add_active_column.sql](sql/add_active_column.sql) - Migration script
- [app.py](app.py) - API endpoint implementations
