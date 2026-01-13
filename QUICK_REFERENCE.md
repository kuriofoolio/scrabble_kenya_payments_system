# Tournament Management - Quick Reference Card

## After Tournament Ends

```bash
# Option 1: API (Recommended)
curl -X POST http://localhost:5000/api/players/deactivate-registered

# Option 2: SQL
sqlite3 instance/sk_tickets.db "UPDATE player SET active = 0 WHERE playerId IN (SELECT DISTINCT playerId FROM ticket);"
```

---

## Before New Tournament

### Keep Previous Tournament Data
```bash
# Activate all players (tickets remain)
curl -X POST http://localhost:5000/api/players/activate-all

# Note: Players with tickets can't register again
```

### Fresh Start (Recommended)
```bash
# 1. Backup database
sqlite3 instance/sk_tickets.db ".backup backup_$(date +%Y%m%d).db"

# 2. Clear tickets
sqlite3 instance/sk_tickets.db "DELETE FROM ticket;"

# 3. Activate all players
curl -X POST http://localhost:5000/api/players/activate-all
```

---

## Quick Status Check

```sql
-- Player status distribution
SELECT active, COUNT(*) as count FROM player GROUP BY active;

-- Current registrations
SELECT COUNT(*) FROM ticket;

-- Revenue
SELECT SUM(totalAmount) FROM payment WHERE paymentStatus = 'Paid';
```

---

## Emergency Commands

```bash
# Activate specific player
sqlite3 instance/sk_tickets.db "UPDATE player SET active = 1 WHERE playerId = X;"

# Remove player's ticket
sqlite3 instance/sk_tickets.db "DELETE FROM ticket WHERE playerId = X;"

# Backup database
sqlite3 instance/sk_tickets.db ".backup backup_emergency_$(date +%Y%m%d_%H%M%S).db"
```

---

## Files Reference

- **Full Guide:** [TOURNAMENT_WORKFLOW.md](TOURNAMENT_WORKFLOW.md)
- **SQL Scripts:** [sql/tournament_management.sql](sql/tournament_management.sql)
- **Migration:** [sql/add_active_column.sql](sql/add_active_column.sql)
