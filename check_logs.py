from database import db

# Check what logs are available for the user
print("Checking user logs...")

try:
    connection = db._get_connection()
    cursor = connection.cursor()
    
    # Get user ID 1 (ANUSHAAZMEERA3) logs
    user_id = 1
    logs = db.get_user_symptom_logs(user_id)
    
    print(f"User ID {user_id} has {len(logs)} logs:")
    
    for i, log in enumerate(logs):
        print(f"  {i+1}. Date: {log.get('selected_date')}")
        print(f"     Symptoms: {log.get('symptoms_selected', 'None')}")
        print(f"     Mood: {log.get('mood_state', 'None')}")
        print(f"     Period: {log.get('had_period', 'None')}")
        print(f"     Pain: {log.get('pain_level', 'None')}")
        print(f"     Notes: {log.get('other_symptom', 'None')}")
        print()
    
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")
