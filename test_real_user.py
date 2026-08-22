from database import db

# Test with real users to see if logs exist
print("Testing with real users...")

try:
    connection = db._get_connection()
    cursor = connection.cursor()
    
    # Get all users
    cursor.execute("SELECT id, username, full_name FROM users ORDER BY id DESC LIMIT 5")
    users = cursor.fetchall()
    
    print(f"Found {len(users)} users:")
    for user in users:
        user_id, username, full_name = user
        print(f"  - {username} (ID: {user_id}) - {full_name}")
        
        # Get logs for this user
        logs = db.get_user_symptom_logs(user_id)
        print(f"    Logs: {len(logs)}")
        
        if logs:
            for i, log in enumerate(logs[:3]):  # Show first 3 logs
                print(f"      {i+1}. Date: {log.get('selected_date')}, Symptoms: {log.get('symptoms_selected', 'None')}, Mood: {log.get('mood_state', 'None')}")
        else:
            print("      No logs found")
    
    # Test specific user if exists
    cursor.execute("SELECT id FROM users WHERE username = 'testuser'")
    test_user = cursor.fetchone()
    
    if test_user:
        test_user_id = test_user[0]
        test_logs = db.get_user_symptom_logs(test_user_id)
        print(f"\nTest user logs: {len(test_logs)}")
        
        if test_logs:
            latest = test_logs[0]
            print(f"Latest: {latest.get('selected_date')} - {latest.get('symptoms_selected')}")
    
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")
