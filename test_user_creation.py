from database import db

# Test user creation
print("Testing user creation...")

# Try to create a test user
result = db.create_user(
    username="testuser123",
    email="test@example.com", 
    password="testpass123",
    full_name="Test User",
    date_of_birth="2000-01-01"
)

print(f"User creation result: {result}")

# Check if user was created
try:
    connection = db._get_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT username, email FROM users")
    users = cursor.fetchall()
    print("Users after creation attempt:")
    for user in users:
        print(f"- Username: {user[0]}, Email: {user[1]}")
    
    connection.close()
    
except Exception as e:
    print(f"Error checking users: {e}")
