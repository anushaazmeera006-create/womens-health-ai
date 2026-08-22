# Test to check if session is working correctly
print("Testing session and user data retrieval...")

# Check if we can get logs for user ID 1 (ANUSHAAZMEERA3)
from database import db

try:
    connection = db._get_connection()
    cursor = connection.cursor()
    
    # Get user ID 1 logs
    user_id = 1
    logs = db.get_user_symptom_logs(user_id)
    
    print(f"User ID 1 (ANUSHAAZMEERA3) has {len(logs)} logs:")
    
    for i, log in enumerate(logs):
        print(f"  {i+1}. Date: {log.get('selected_date')}")
        print(f"     Symptoms: {log.get('symptoms_selected', 'None')}")
        print(f"     Mood: {log.get('mood_state', 'None')}")
        print(f"     Period: {log.get('had_period', 'None')}")
        print(f"     Pain: {log.get('pain_level', 'None')}")
        print()
    
    # Test pattern insights for this user
    from app import calculate_pattern_insights
    pattern_insights = calculate_pattern_insights(logs)
    
    if pattern_insights:
        print("Pattern Insights:")
        print(f"  Common symptoms: {pattern_insights.get('common_symptoms', [])}")
        print(f"  Mood distribution: {pattern_insights.get('mood_distribution', [])}")
        print(f"  Cycle phases: {pattern_insights.get('cycle_phases', [])}")
        print(f"  Avg pain: {pattern_insights.get('avg_pain', 0)}")
    else:
        print("No pattern insights calculated")
    
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")
