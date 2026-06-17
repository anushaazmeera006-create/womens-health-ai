import os
import psycopg2

def init_postgresql_tables():
    """Initialize PostgreSQL database tables"""
    
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
    
    if not db_url:
        print("ERROR: DATABASE_URL or POSTGRES_URL environment variable not set")
        return False
    
    try:
        # Connect to PostgreSQL
        connection = psycopg2.connect(db_url)
        cursor = connection.cursor()
        
        print("Connected to PostgreSQL database")
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                date_of_birth DATE,
                mobile_number VARCHAR(20) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Users table created/verified")
        
        # Create symptom_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS symptom_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                selected_date DATE NOT NULL,
                had_period VARCHAR(10) DEFAULT 'No',
                cycle_phase VARCHAR(50) DEFAULT 'Follicular',
                symptoms_selected TEXT,
                other_symptom TEXT,
                mood_state TEXT,
                cramps BOOLEAN DEFAULT FALSE,
                fatigue BOOLEAN DEFAULT FALSE,
                nausea BOOLEAN DEFAULT FALSE,
                mood_swings BOOLEAN DEFAULT FALSE,
                acne BOOLEAN DEFAULT FALSE,
                back_pain BOOLEAN DEFAULT FALSE,
                flow_intensity INTEGER DEFAULT 2,
                pain_level INTEGER DEFAULT 2,
                cluster_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, selected_date)
            )
        ''')
        print("✅ Symptom logs table created/verified")
        
        # Create period_dates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS period_dates (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                period_date DATE NOT NULL,
                period_length_days INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, period_date)
            )
        ''')
        print("✅ Period dates table created/verified")
        
        # Create assessment_results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessment_results (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                assessment_type VARCHAR(100) NOT NULL,
                risk_percentage DECIMAL(5,2),
                risk_level VARCHAR(50),
                risk_factors TEXT,
                assessment_summary TEXT,
                recommendations TEXT,
                assessment_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        print("✅ Assessment results table created/verified")
        
        # Commit changes
        connection.commit()
        print("\n✅ All database tables initialized successfully!")
        
        # Close connection
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"ERROR initializing database: {e}")
        return False

if __name__ == "__main__":
    print("Initializing PostgreSQL database tables...")
    success = init_postgresql_tables()
    if success:
        print("\n✅ Database initialization completed successfully!")
    else:
        print("\n❌ Database initialization failed!")
