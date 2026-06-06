#!/usr/bin/env python3
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager

def check_current_logs():
    """Check what logs currently exist in the database"""
    db = DatabaseManager()
    
    # Get all logs for user 6
    logs = db.get_user_symptom_logs(6)
    
    print(f"Found {len(logs)} logs for user 6:")
    for log in logs:
        print(f"  Date: {log.get('selected_date')}, Period: {log.get('had_period')}")
    
    # Check specifically for menstrual logs
    menstrual_logs = [log for log in logs if log.get('had_period') == 'Yes']
    print(f"\nFound {len(menstrual_logs)} menstrual logs:")
    for log in menstrual_logs:
        print(f"  Date: {log.get('selected_date')}")

if __name__ == "__main__":
    check_current_logs()
