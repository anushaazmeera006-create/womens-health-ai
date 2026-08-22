from database import db

# Clear all users and test with fresh data
try:
    connection = db._get_connection()
    cursor = connection.cursor()
    
    print("Clearing all users...")
    cursor.execute("DELETE FROM users")
    cursor.execute("ALTER TABLE users AUTO_INCREMENT = 1")
    connection.commit()
    
    print("Testing with new user...")
    
    # Test with completely new username
    result = db.create_user_new(
        username="anusha123",
        password="mypassword123",
        full_name="Anusha",
        mobile_number="9876543210"
    )
    
    print(f"User creation result: {result}")
    
    if result:
        print("✅ User created successfully!")
        
        # Test authentication
        auth_result = db.authenticate_user("anusha123", "mypassword123")
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
    
    # Check current users
    cursor.execute("SELECT username, full_name, mobile_number FROM users")
    users = cursor.fetchall()
    
    print(f"\nCurrent users in database ({len(users)}):")
    for user in users:
        print(f"- {user[0]} ({user[1]}) - {user[2]}")
    
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")
