from database import db

# Test Health History page data retrieval
print("Testing Health History page data retrieval...")

try:
    # Get user ID from a real user
    connection = db._get_connection()
    cursor = connection.cursor()
    
    # Get a user (you can change this to test different users)
    cursor.execute("SELECT id, username FROM users WHERE username = 'testuser'")
    user_result = cursor.fetchone()
    
    if user_result:
        user_id = user_result[0]
        print(f"✅ Found user: testuser (ID: {user_id})")
        
        # Get logs for this user
        logs = db.get_user_symptom_logs(user_id)
        print(f"✅ Retrieved {len(logs)} logs for user")
        
        if logs:
            latest_log = logs[0]
            print(f"Latest log date: {latest_log.get('selected_date')}")
            print(f"Latest log symptoms: {latest_log.get('symptoms_selected', 'None')}")
            print(f"Latest log mood: {latest_log.get('mood_state', 'None')}")
            
            # Test pattern insights calculation
            from app import calculate_pattern_insights
            pattern_insights = calculate_pattern_insights(logs)
            
            if pattern_insights:
                print(f"✅ Pattern insights calculated:")
                print(f"  Common symptoms: {len(pattern_insights.get('common_symptoms', []))}")
                print(f"  Mood distribution: {len(pattern_insights.get('mood_distribution', []))}")
                print(f"  Cycle phases: {len(pattern_insights.get('cycle_phases', []))}")
                print(f"  Pain trends: {pattern_insights.get('avg_pain', 0)}")
            else:
                print("❌ No pattern insights calculated")
        else:
            print("❌ No logs found for user")
    else:
        print("❌ User 'testuser' not found")
    
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")
