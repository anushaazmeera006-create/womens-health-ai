-- Check database connection and show current database
SELECT DATABASE() as current_database;

-- Show all tables in the database
SHOW TABLES;

-- Check if users table exists and show structure
DESCRIBE users;

-- Check if any users exist
SELECT COUNT(*) as user_count FROM users;
