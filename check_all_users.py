#!/usr/bin/env python3
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager

def check_all_users():
    """Check all users and their logs"""
    db = DatabaseManager()
    
    # Try different user IDs to find the 2026-04-13 log
    for user_id in range(1, 11):
        logs = db.get_user_symptom_logs(user_id)
        if logs:
            print(f"User {user_id}: Found {len(logs)} logs")
            for log in logs:
                if log.get('selected_date') == '2026-04-13':
                    print(f"  FOUND 2026-04-13 log for user {user_id}!")
                    print(f"  Period: {log.get('had_period')}")
                    return user_id
        else:
            print(f"User {user_id}: No logs")
    
    print("2026-04-13 log not found in any user (1-10)")
    return None

if __name__ == "__main__":
    user_id = check_all_users()
    if user_id:
        print(f"\nThe 2026-04-13 log belongs to user {user_id}")
    else:
        print("\nNo 2026-04-13 log found in database")
