from database import db

# Clear all user data completely
try:
    connection = db._get_connection()
    cursor = connection.cursor()
    
    print("Clearing ALL user data...")
    
    # Delete everything from users table
    cursor.execute("DELETE FROM users")
    
    # Reset auto-increment
    cursor.execute("ALTER TABLE users AUTO_INCREMENT = 1")
    
    # Check if table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    connection.commit()
    
    print(f"Users table cleared! Current count: {user_count}")
    print("Database is now completely fresh for new users")
    
    connection.close()
    
except Exception as e:
    print(f"Error clearing users: {e}")
