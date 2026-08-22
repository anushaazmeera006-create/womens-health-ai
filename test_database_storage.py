from database import db
import json
from datetime import datetime, timedelta

# Test database storage for 30-40 days of logs
print("Testing database storage for 30-40 days of logs...")

try:
    # Create a test user
    print("Creating test user...")
    user_result = db.create_user_new(
        username="testuser",
        password="password123",
        full_name="Test User",
        mobile_number="1234567890"
    )
    
    if user_result:
        # Get user ID
        connection = db._get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", ("testuser",))
        user_id = cursor.fetchone()[0]
        print(f"User created with ID: {user_id}")
        
        # Simulate 35 days of symptom logs
        print("\nCreating 35 days of symptom logs...")
        
        for day in range(35):
            date = (datetime.now() - timedelta(days=day)).strftime("%Y-%m-%d")
            
            # Create varied symptom data
            log_data = {
                'selected_date': date,
                'had_period': 'Yes' if day % 28 < 5 else 'No',  # Period every 28 days
                'cycle_phase': ['Follicular', 'Ovulation', 'Luteal', 'Menstrual'][day % 4],
                'symptoms_selected': ['Fatigue', 'Mood swings'] if day % 7 < 3 else ['Cramps', 'Headache'],
                'other_symptom': 'Stress' if day % 10 == 0 else '',
                'mood_state': ['Happy', 'Anxious', 'Irritated', 'Calm'][day % 4],
                'cramps': True if day % 28 < 5 else False,
                'fatigue': True if day % 7 < 3 else False,
                'nausea': False,
                'mood_swings': True if day % 7 < 3 else False,
                'acne': True if day % 14 < 7 else False,
                'back_pain': True if day % 28 < 5 else False,
                'flow_intensity': 3 if day % 28 < 5 else 1,
                'pain_level': 4 if day % 28 < 5 else 2,
                'cluster_result': f'Day {day + 1} Pattern'
            }
            
            # Save to database
            success = db.save_symptom_log(user_id, log_data)
            if success:
                print(f"Day {day + 1} ({date}): Saved")
            else:
                print(f"Day {day + 1} ({date}): Failed to save")
        
        # Check how many logs were stored
        logs = db.get_user_symptom_logs(user_id)
        print(f"\nTotal logs stored: {len(logs)}")
        
        if len(logs) >= 30:
            print("SUCCESS: Database stored 30+ days of logs!")
            
            # Show pattern analysis capability
            print("\nPattern Analysis Data Available:")
            print(f"- Date range: {logs[-1]['selected_date']} to {logs[0]['selected_date']}")
            print(f"- Symptom types: {len(set([log['symptoms_selected'] for log in logs]))}")
            print(f"- Cycle phases: {len(set([log['cycle_phase'] for log in logs]))}")
            print(f"- Mood states: {len(set([log['mood_state'] for log in logs]))}")
            
            print("\nPattern Analysis Features:")
            print("1. Symptom clustering (High/Low symptom days)")
            print("2. Cycle phase tracking")
            print("3. Mood pattern analysis")
            print("4. Period prediction")
            print("5. Risk assessment")
            
        else:
            print("ERROR: Not enough logs stored for pattern analysis")
        
        connection.close()
        
    else:
        print("Failed to create test user")
        
except Exception as e:
    print(f"Error: {e}")
