-- PRAGMA foreign_keys = OFF;

-- DROP TABLE IF EXISTS player;
-- DROP TABLE IF EXISTS division;
-- DROP TABLE IF EXISTS ticket;
-- DROP TABLE IF EXISTS pushrequest;
-- DROP TABLE IF EXISTS payment;
-- -- Add other table names you know exist

-- PRAGMA foreign_keys = ON;

-- sqlite3 instance/sk_tickets.db < sql/delete_data.sql 
delete from ticket; delete from pushrequest; delete from payment;