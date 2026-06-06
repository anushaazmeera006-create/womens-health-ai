from database import db

# Clear user data but keep period dates
try:
    connection = db._get_connection()
    cursor = connection.cursor()
    
    print("Clearing user data...")
    
    # Clear symptom logs (will be recreated with new users)
    cursor.execute("DELETE FROM symptom_logs")
    
    # Clear assessment results (will be recreated with new users)
    cursor.execute("DELETE FROM assessment_results")
    
    # Clear users table
    cursor.execute("DELETE FROM users")
    
    # Keep period dates as requested
    cursor.execute("SELECT COUNT(*) FROM period_dates")
    period_count = cursor.fetchone()[0]
    print(f"Kept {period_count} period dates")
    
    connection.commit()
    
    print("User data cleared successfully!")
    print("Period dates preserved as requested")
    
    connection.close()
    
except Exception as e:
    print(f"Error clearing user data: {e}")
