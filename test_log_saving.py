from database import db
from datetime import datetime, timedelta
import json

# Test log saving and retrieval
print("Testing log saving and retrieval...")

# Create a test user first
try:
    # Clear existing test user
    connection = db._get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM users WHERE username = 'testuser'")
    connection.commit()
    
    # Create test user
    success = db.create_user_new(
        username="testuser",
        password="password123",
        full_name="Test User",
        mobile_number="1234567890"
    )
    
    if success:
        cursor.execute("SELECT id FROM users WHERE username = 'testuser'")
        user_id = cursor.fetchone()[0]
        print(f"✅ Test user created with ID: {user_id}")
        
        # Create test log entry
        log_data = {
            'selected_date': datetime.now().strftime('%Y-%m-%d'),
            'had_period': 'No',
            'cycle_phase': 'Follicular',
            'symptoms_selected': ['Fatigue', 'Headache'],
            'other_symptom': 'Feeling tired today',
            'mood_state': 'Anxious',
            'cramps': False,
            'fatigue': True,
            'nausea': False,
            'mood_swings': False,
            'acne': False,
            'back_pain': False,
            'flow_intensity': 2,
            'pain_level': 3,
            'cluster_result': '😟 Low Energy Day'
        }
        
        # Save log
        save_success = db.save_symptom_log(user_id, log_data)
        print(f"Log save result: {save_success}")
        
        # Retrieve logs immediately
        retrieved_logs = db.get_user_symptom_logs(user_id)
        print(f"Retrieved {len(retrieved_logs)} logs")
        
        if retrieved_logs:
            latest_log = retrieved_logs[0]
            print(f"Latest log: {latest_log}")
            print(f"Symptoms: {latest_log.get('symptoms_selected', 'None')}")
            print(f"Mood: {latest_log.get('mood_state', 'None')}")
            print(f"Date: {latest_log.get('selected_date', 'None')}")
        
        # Test pattern insights calculation
        if len(retrieved_logs) >= 1:
            from collections import Counter
            
            # Calculate pattern insights manually
            all_symptoms = []
            moods = []
            phases = []
            pain_levels = []
            
            for log in retrieved_logs:
                symptoms = log.get('symptoms_selected', '[]')
                if isinstance(symptoms, str):
                    if symptoms.startswith('['):
                        symptoms = json.loads(symptoms)
                    else:
                        symptoms = symptoms.split(',')
                    all_symptoms.extend([s.strip() for s in symptoms if s.strip()])
                
                moods.append(log.get('mood_state', ''))
                phases.append(log.get('cycle_phase', ''))
                pain_levels.append(log.get('pain_level', 0))
            
            symptom_counts = Counter(all_symptoms)
            mood_counts = Counter(moods)
            phase_counts = Counter(phases)
            
            print(f"\nPattern Analysis:")
            print(f"Symptom counts: {dict(symptom_counts.most_common(5))}")
            print(f"Mood distribution: {dict(mood_counts)}")
            print(f"Phase distribution: {dict(phase_counts)}")
            print(f"Average pain: {sum(pain_levels) / len(pain_levels):.1f}")
        
    else:
        print("❌ Failed to create test user")
    
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")
