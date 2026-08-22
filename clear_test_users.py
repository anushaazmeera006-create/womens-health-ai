from database import db

# Clear test users from database
try:
    connection = db._get_connection()
    cursor = connection.cursor()
    
    # Delete test users
    cursor.execute("DELETE FROM users WHERE username LIKE 'test%'")
    connection.commit()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"Users in database after cleanup: {user_count}")
    
    connection.close()
    
except Exception as e:
    print(f"Error clearing test users: {e}")
