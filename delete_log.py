#!/usr/bin/env python3
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager

def delete_specific_log():
    """Delete the 2026-04-13 log from the database"""
    db = DatabaseManager()
    
    # Delete the log for 2026-04-13
    success = db.delete_symptom_log(6, "2026-04-13")  # Assuming user_id is 6
    
    if success:
        print("Successfully deleted log for 2026-04-13")
    else:
        print("Failed to delete log for 2026-04-13")
    
    return success

if __name__ == "__main__":
    delete_specific_log()
