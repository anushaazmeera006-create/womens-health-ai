from database import db

# Test the new signup process
print("Testing new signup process...")

# Test creating a user
result = db.create_user_new(
    username="testuser123",
    password="password123",
    full_name="Test User",
    mobile_number="1234567890"
)

print(f"User creation result: {result}")

if result:
    print("✅ User created successfully!")
    
    # Test authentication
    auth_result = db.authenticate_user("testuser123", "password123")
    print(f"Authentication result: {auth_result}")
    
    if auth_result:
        print("✅ Authentication successful!")
        print(f"User ID: {auth_result['id']}")
        print(f"Username: {auth_result['username']}")
        print(f"Full Name: {auth_result['full_name']}")
    else:
        print("❌ Authentication failed!")
else:
    print("❌ User creation failed!")

# Check current users in database
try:
    connection = db._get_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT username, full_name, mobile_number FROM users")
    users = cursor.fetchall()
    
    print(f"\nCurrent users in database ({len(users)}):")
    for user in users:
        print(f"- {user[0]} ({user[1]}) - {user[2]}")
    
    connection.close()
    
except Exception as e:
    print(f"Error checking users: {e}")
