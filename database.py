import mysql.connector
from mysql.connector import Error
import hashlib
import json
from datetime import datetime, date
from typing import Optional, Dict, List, Any
import os

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Connect to MySQL database"""
        try:
            # Use environment variables for deployment, fallback to local for development
            host = os.getenv('DATABASE_HOST', 'localhost')
            user = os.getenv('DATABASE_USER', 'root')
            password = os.getenv('DATABASE_PASSWORD', 'Anusha@2006')
            database = os.getenv('DATABASE_NAME', 'womens_health_ai')
            port = os.getenv('DATABASE_PORT', '3306')
            
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port
            )
            if self.connection.is_connected():
                print(f"Connected to MySQL database: host={host}, user={user}, database={database}, port={port}")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            # For development, create a local SQLite fallback
            self._create_sqlite_fallback()
    
    def _create_sqlite_fallback(self):
        """Fallback to SQLite for development"""
        import sqlite3
        self.use_sqlite = True
        self.sqlite_path = 'womens_health_ai.db'
        print("Using SQLite fallback database")
        self._init_sqlite_tables()
    
    def _init_sqlite_tables(self):
        """Initialize SQLite tables"""
        import sqlite3
        connection = sqlite3.connect(self.sqlite_path)
        cursor = connection.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                date_of_birth DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Symptom logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS symptom_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                selected_date DATE NOT NULL,
                had_period TEXT DEFAULT 'No',
                cycle_phase TEXT DEFAULT 'Follicular',
                symptoms_selected TEXT,
                other_symptom TEXT,
                mood_state TEXT,
                cramps BOOLEAN DEFAULT 0,
                fatigue BOOLEAN DEFAULT 0,
                nausea BOOLEAN DEFAULT 0,
                mood_swings BOOLEAN DEFAULT 0,
                acne BOOLEAN DEFAULT 0,
                back_pain BOOLEAN DEFAULT 0,
                flow_intensity INTEGER DEFAULT 2,
                pain_level INTEGER DEFAULT 2,
                cluster_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, selected_date)
            )
        ''')
        
        # Period dates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS period_dates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                period_date DATE NOT NULL,
                period_length_days INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, period_date)
            )
        ''')
        
        # Assessment results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessment_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                assessment_type TEXT NOT NULL,
                risk_percentage REAL,
                risk_level TEXT,
                risk_factors TEXT,
                assessment_summary TEXT,
                recommendations TEXT,
                assessment_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        connection.commit()
        connection.close()
    
    def _get_connection(self):
        """Get database connection (thread-safe)"""
        if hasattr(self, 'use_sqlite') and self.use_sqlite:
            import sqlite3
            connection = sqlite3.connect(self.sqlite_path)
            connection.row_factory = sqlite3.Row
            return connection
        else:
            # Create fresh MySQL connection for each operation
            host = os.getenv('DATABASE_HOST', 'localhost')
            user = os.getenv('DATABASE_USER', 'root')
            password = os.getenv('DATABASE_PASSWORD', 'Anusha@2006')
            database = os.getenv('DATABASE_NAME', 'womens_health_ai')
            port = os.getenv('DATABASE_PORT', '3306')
            
            return mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port
            )
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, email: str, password: str, full_name: str = None, date_of_birth: str = None) -> bool:
        """Create a new user"""
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            password_hash = self.hash_password(password)
            
            # Check if user already exists
            check_query = '''
                SELECT username, email FROM users 
                WHERE username = ? OR email = ?
            ''' if hasattr(connection, 'row_factory') else '''
                SELECT username, email FROM users 
                WHERE username = %s OR email = %s
            '''
            
            cursor.execute(check_query, (username, email))
            existing_user = cursor.fetchone()
            
            if existing_user:
                if hasattr(connection, 'row_factory'):
                    existing = dict(existing_user)
                    if existing['username'] == username:
                        print(f"Username '{username}' already exists")
                    if existing['email'] == email:
                        print(f"Email '{email}' already exists")
                else:
                    if existing_user[0] == username:
                        print(f"Username '{username}' already exists")
                    if existing_user[1] == email:
                        print(f"Email '{email}' already exists")
                return False
            
            # Create new user
            query = '''
                INSERT INTO users (username, email, password_hash, full_name, date_of_birth)
                VALUES (?, ?, ?, ?, ?)
            ''' if hasattr(connection, 'row_factory') else '''
                INSERT INTO users (username, email, password_hash, full_name, date_of_birth)
                VALUES (%s, %s, %s, %s, %s)
            '''
            
            cursor.execute(query, (username, email, password_hash, full_name, date_of_birth))
            connection.commit()
            print(f"User '{username}' created successfully")
            return True
        except Error as e:
            print(f"Database error creating user: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error creating user: {e}")
            return False
        finally:
            if hasattr(connection, 'close'):
                connection.close()
    
    def create_user_new(self, username: str, password: str, full_name: str, mobile_number: str) -> bool:
        """Create a new user with new fields (no email required)"""
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            password_hash = self.hash_password(password)
            
            # Check if username already exists
            check_query = '''
                SELECT username FROM users 
                WHERE username = %s
            ''' if not hasattr(connection, 'row_factory') else '''
                SELECT username FROM users 
                WHERE username = ?
            '''
            
            cursor.execute(check_query, (username,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                print(f"Username '{username}' already exists")
                return False
            
            # Check if mobile number already exists
            check_mobile_query = '''
                SELECT mobile_number FROM users 
                WHERE mobile_number = %s
            ''' if not hasattr(connection, 'row_factory') else '''
                SELECT mobile_number FROM users 
                WHERE mobile_number = ?
            '''
            
            cursor.execute(check_mobile_query, (mobile_number,))
            existing_mobile = cursor.fetchone()
            
            if existing_mobile:
                print(f"Mobile number '{mobile_number}' already exists")
                return False
            
            # Create new user
            query = '''
                INSERT INTO users (username, password_hash, full_name, mobile_number)
                VALUES (%s, %s, %s, %s)
            ''' if not hasattr(connection, 'row_factory') else '''
                INSERT INTO users (username, password_hash, full_name, mobile_number)
                VALUES (?, ?, ?, ?)
            '''
            
            cursor.execute(query, (username, password_hash, full_name, mobile_number))
            connection.commit()
            print(f"User '{username}' created successfully")
            return True
        except Error as e:
            print(f"Database error creating user: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error creating user: {e}")
            return False
        finally:
            if hasattr(connection, 'close'):
                connection.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data"""
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            password_hash = self.hash_password(password)
            
            query = '''
                SELECT id, username, email, full_name, date_of_birth, mobile_number
                FROM users 
                WHERE username = %s AND password_hash = %s
            ''' if not hasattr(connection, 'row_factory') else '''
                SELECT id, username, email, full_name, date_of_birth, mobile_number
                FROM users 
                WHERE username = ? AND password_hash = ?
            '''
            
            cursor.execute(query, (username, password_hash))
            result = cursor.fetchone()
            
            if result:
                if hasattr(connection, 'row_factory'):
                    return dict(result)
                else:
                    return {
                        'id': result[0],
                        'username': result[1],
                        'email': result[2],
                        'full_name': result[3],
                        'date_of_birth': result[4],
                        'mobile_number': result[5]
                    }
            return None
        except Error as e:
            print(f"Error authenticating user: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error authenticating user: {e}")
            return None
        finally:
            if hasattr(connection, 'close'):
                connection.close()
    
    def save_symptom_log(self, user_id: int, log_data: Dict) -> bool:
        """Save symptom log to database"""
        connection = self._get_connection()
        cursor = None
        try:
            cursor = connection.cursor()
            
            query = '''
                INSERT INTO symptom_logs 
                (user_id, selected_date, had_period, cycle_phase, symptoms_selected, 
                other_symptom, mood_state, cramps, fatigue, nausea, mood_swings, 
                acne, back_pain, flow_intensity, pain_level, cluster_result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON DUPLICATE KEY UPDATE
                had_period = VALUES(had_period),
                cycle_phase = VALUES(cycle_phase),
                symptoms_selected = VALUES(symptoms_selected),
                other_symptom = VALUES(other_symptom),
                mood_state = VALUES(mood_state),
                cramps = VALUES(cramps),
                fatigue = VALUES(fatigue),
                nausea = VALUES(nausea),
                mood_swings = VALUES(mood_swings),
                acne = VALUES(acne),
                back_pain = VALUES(back_pain),
                flow_intensity = VALUES(flow_intensity),
                pain_level = VALUES(pain_level),
                cluster_result = VALUES(cluster_result)
            ''' if hasattr(connection, 'row_factory') else '''
                INSERT INTO symptom_logs 
                (user_id, selected_date, had_period, cycle_phase, symptoms_selected, 
                other_symptom, mood_state, cramps, fatigue, nausea, mood_swings, 
                acne, back_pain, flow_intensity, pain_level, cluster_result)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                had_period = VALUES(had_period),
                cycle_phase = VALUES(cycle_phase),
                symptoms_selected = VALUES(symptoms_selected),
                other_symptom = VALUES(other_symptom),
                mood_state = VALUES(mood_state),
                cramps = VALUES(cramps),
                fatigue = VALUES(fatigue),
                nausea = VALUES(nausea),
                mood_swings = VALUES(mood_swings),
                acne = VALUES(acne),
                back_pain = VALUES(back_pain),
                flow_intensity = VALUES(flow_intensity),
                pain_level = VALUES(pain_level),
                cluster_result = VALUES(cluster_result)
            '''
            
            cursor.execute(query, (
                user_id,
                log_data.get("selected_date"),
                log_data.get("had_period"),
                log_data.get("cycle_phase"),
                json.dumps(log_data.get("symptoms_selected", [])),
                log_data.get("other_symptom"),
                log_data.get("mood_state"),
                log_data.get("cramps", False),
                log_data.get("fatigue", False),
                log_data.get("nausea", False),
                log_data.get("mood_swings", False),
                log_data.get("acne", False),
                log_data.get("back_pain", False),
                log_data.get("flow_intensity", 2),
                log_data.get("pain_level", 2),
                log_data.get("cluster_result", "")
            ))
            
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error saving symptom log: {e}")
            if cursor:
                cursor.close()
            return False
        finally:
            if hasattr(connection, 'close'):
                connection.close()
    
    def get_user_symptom_logs(self, user_id: int, limit: int = None) -> List[Dict]:
        """Get all symptom logs for a user"""
        connection = self._get_connection()
        cursor = None
        try:
            cursor = connection.cursor()
            
            query = '''
                SELECT * FROM symptom_logs 
                WHERE user_id = ? 
                ORDER BY selected_date DESC
            ''' if hasattr(connection, 'row_factory') else '''
                SELECT * FROM symptom_logs 
                WHERE user_id = %s 
                ORDER BY selected_date DESC
            '''
            
            params = (user_id,)
            if limit:
                query += ' LIMIT ?' if hasattr(connection, 'row_factory') else ' LIMIT %s'
                params = (user_id, limit)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            logs = []
            for result in results:
                if hasattr(connection, 'row_factory'):
                    log = dict(result)
                    if log['symptoms_selected']:
                        log['symptoms_selected'] = json.loads(log['symptoms_selected'])
                else:
                    log = {
                        'id': result[0], 'user_id': result[1], 'selected_date': result[2],
                        'had_period': result[3], 'cycle_phase': result[4],
                        'symptoms_selected': json.loads(result[5]) if result[5] else [],
                        'other_symptom': result[6], 'mood_state': result[7],
                        'cramps': bool(result[8]), 'fatigue': bool(result[9]),
                        'nausea': bool(result[10]), 'mood_swings': bool(result[11]),
                        'acne': bool(result[12]), 'back_pain': bool(result[13]),
                        'flow_intensity': result[14], 'pain_level': result[15],
                        'cluster_result': result[16], 'created_at': result[17]
                    }
                logs.append(log)
            
            return logs
        except Error as e:
            print(f"Error getting symptom logs: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if hasattr(connection, 'close'):
                connection.close()
    
    def save_period_date(self, user_id: int, period_date: str, period_length_days: int = 5) -> bool:
        """Save period date for user"""
        try:
            cursor = self.connection.cursor()
            
            query = '''
                INSERT OR REPLACE INTO period_dates (user_id, period_date, period_length_days)
                VALUES (?, ?, ?)
            ''' if hasattr(self.connection, 'row_factory') else '''
                INSERT INTO period_dates (user_id, period_date, period_length_days)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                period_length_days = VALUES(period_length_days)
            '''
            
            cursor.execute(query, (user_id, period_date, period_length_days))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error saving period date: {e}")
            return False
    
    def get_user_period_dates(self, user_id: int) -> List[str]:
        """Get all period dates for a user"""
        try:
            cursor = self.connection.cursor()
            
            query = '''
                SELECT period_date FROM period_dates 
                WHERE user_id = ? 
                ORDER BY period_date DESC
            ''' if hasattr(self.connection, 'row_factory') else '''
                SELECT period_date FROM period_dates 
                WHERE user_id = %s 
                ORDER BY period_date DESC
            '''
            
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            
            return [result[0] for result in results]
        except Error as e:
            print(f"Error getting period dates: {e}")
            return []
    
    def delete_symptom_log(self, user_id: int, selected_date: str) -> bool:
        """Delete a specific symptom log from database"""
        connection = self._get_connection()
        cursor = None
        try:
            cursor = connection.cursor()
            
            # First check if the log exists
            check_query = '''
                SELECT selected_date, had_period FROM symptom_logs 
                WHERE user_id = ? AND selected_date = ?
            ''' if hasattr(connection, 'row_factory') else '''
                SELECT selected_date, had_period FROM symptom_logs 
                WHERE user_id = %s AND selected_date = %s
            '''
            
            cursor.execute(check_query, (user_id, selected_date))
            existing_log = cursor.fetchone()
            print(f"DELETE DEBUG: Looking for log - User: {user_id}, Date: {selected_date}")
            print(f"DELETE DEBUG: Existing log found: {existing_log}")
            
            if not existing_log:
                print("DELETE DEBUG: No log found to delete")
                return False
            
            query = '''
                DELETE FROM symptom_logs 
                WHERE user_id = ? AND selected_date = ?
            ''' if hasattr(connection, 'row_factory') else '''
                DELETE FROM symptom_logs 
                WHERE user_id = %s AND selected_date = %s
            '''
            
            cursor.execute(query, (user_id, selected_date))
            rows_affected = cursor.rowcount
            print(f"DELETE DEBUG: Rows affected by delete: {rows_affected}")
            
            connection.commit()
            cursor.close()
            
            return rows_affected > 0
        except Error as e:
            print(f"Error deleting symptom log: {e}")
            if cursor:
                cursor.close()
            return False
        finally:
            if hasattr(connection, 'close'):
                connection.close()
    
    def delete_period_date(self, user_id: int, period_date: str) -> bool:
        """Delete a specific period date from database"""
        connection = self._get_connection()
        cursor = None
        try:
            cursor = connection.cursor()
            
            query = '''
                DELETE FROM period_dates 
                WHERE user_id = ? AND period_date = ?
            ''' if hasattr(connection, 'row_factory') else '''
                DELETE FROM period_dates 
                WHERE user_id = %s AND period_date = %s
            '''
            
            cursor.execute(query, (user_id, period_date))
            rows_affected = cursor.rowcount
            connection.commit()
            cursor.close()
            
            return rows_affected > 0
        except Error as e:
            print(f"Error deleting period date: {e}")
            if cursor:
                cursor.close()
            return False
        finally:
            if hasattr(connection, 'close'):
                connection.close()
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()

# Global database instance
db = DatabaseManager()
