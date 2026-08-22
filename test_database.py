from database import db

# Test database connection and check tables
try:
    connection = db._get_connection()
    cursor = connection.cursor()
    
    # Check if users table exists
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    print("Tables in database:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Check if users table exists and has data
    if 'users' in [table[0] for table in tables]:
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"\nNumber of users in database: {user_count}")
        
        cursor.execute("SELECT username, email FROM users")
        users = cursor.fetchall()
        print("Existing users:")
        for user in users:
            print(f"- Username: {user[0]}, Email: {user[1]}")
    else:
        print("\n'users' table does not exist!")
    
    connection.close()
    
except Exception as e:
    print(f"Error testing database: {e}")
