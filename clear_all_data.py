from database import db

# Clear all user data completely from all tables
try:
    connection = db._get_connection()
    cursor = connection.cursor()
    
    print("Clearing ALL user data from all tables...")
    
    # Delete from symptom_logs table
    cursor.execute("DELETE FROM symptom_logs")
    print("Symptom logs table cleared")
    
    # Delete from period_dates table
    cursor.execute("DELETE FROM period_dates")
    print("Period dates table cleared")
    
    # Delete from users table
    cursor.execute("DELETE FROM users")
    print("Users table cleared")
    
    # Reset auto-increment for users table
    cursor.execute("ALTER TABLE users AUTO_INCREMENT = 1")
    
    # Check if tables are empty
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM symptom_logs")
    log_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM period_dates")
    period_count = cursor.fetchone()[0]
    
    connection.commit()
    
    print(f"Database cleared! Users: {user_count}, Logs: {log_count}, Period dates: {period_count}")
    print("Database is now completely fresh for new users")
    
    connection.close()
    
except Exception as e:
    print(f"Error clearing data: {e}")
