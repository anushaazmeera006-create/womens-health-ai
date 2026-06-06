from database import db

# Fix database column sizes
try:
    connection = db._get_connection()
    cursor = connection.cursor()
    
    print("Fixing database column sizes...")
    
    # Fix mood_state column size
    cursor.execute("ALTER TABLE symptom_logs MODIFY COLUMN mood_state VARCHAR(50)")
    print("Fixed mood_state column size")
    
    # Fix other columns if needed
    cursor.execute("ALTER TABLE symptom_logs MODIFY COLUMN cycle_phase VARCHAR(20)")
    print("Fixed cycle_phase column size")
    
    cursor.execute("ALTER TABLE symptom_logs MODIFY COLUMN symptoms_selected TEXT")
    print("Fixed symptoms_selected column size")
    
    cursor.execute("ALTER TABLE symptom_logs MODIFY COLUMN other_symptom TEXT")
    print("Fixed other_symptom column size")
    
    cursor.execute("ALTER TABLE symptom_logs MODIFY COLUMN cluster_result TEXT")
    print("Fixed cluster_result column size")
    
    connection.commit()
    print("Database columns fixed successfully!")
    
    connection.close()
    
except Exception as e:
    print(f"Error fixing database: {e}")
