from database import db

# Update database schema to remove email requirement and add mobile number
try:
    connection = db._get_connection()
    cursor = connection.cursor()
    
    print("Updating database schema...")
    
    # Check if mobile_number column exists
    cursor.execute("SHOW COLUMNS FROM users LIKE 'mobile_number'")
    mobile_column = cursor.fetchone()
    
    if not mobile_column:
        # Add mobile_number column
        cursor.execute("ALTER TABLE users ADD COLUMN mobile_number VARCHAR(20) UNIQUE")
        print("Added mobile_number column")
    
    # Make email column nullable (remove requirement)
    cursor.execute("ALTER TABLE users MODIFY COLUMN email VARCHAR(100) NULL")
    print("Made email column nullable")
    
    # Create new users table structure if needed
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_new (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100),
            mobile_number VARCHAR(20) UNIQUE,
            date_of_birth DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    print("Database schema updated successfully!")
    
    connection.close()
    
except Exception as e:
    print(f"Error updating database schema: {e}")
