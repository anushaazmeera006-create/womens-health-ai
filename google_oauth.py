import os
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import google.auth
from flask import session, redirect, url_for
import requests
import json

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID_HERE")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET_HERE")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

class GoogleOAuth:
    def __init__(self):
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.scopes = ["openid", "email", "profile"]
    
    def get_flow(self, redirect_uri):
        """Create OAuth flow for authentication"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://accounts.google.com/o/oauth2/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=self.scopes,
            redirect_uri=redirect_uri
        )
        return flow
    
    def get_user_info(self, credentials):
        """Get user information from Google"""
        try:
            userinfo_endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"
            access_token = credentials.token
            
            response = requests.get(
                userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None
    
    def create_or_update_user(self, user_info):
        """Create or update user in database based on Google info"""
        from database import db
        
        try:
            email = user_info.get("email")
            name = user_info.get("name", "")
            picture = user_info.get("picture", "")
            google_id = user_info.get("id")
            
            # Check if user exists by email
            connection = db._get_connection()
            cursor = connection.cursor()
            
            check_query = '''
                SELECT id, username, full_name FROM users 
                WHERE email = %s
            ''' if not hasattr(connection, 'row_factory') else '''
                SELECT id, username, full_name FROM users 
                WHERE email = ?
            '''
            
            cursor.execute(check_query, (email,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # User exists, update Google info
                if hasattr(connection, 'row_factory'):
                    user_data = dict(existing_user)
                    user_id = user_data['id']
                    username = user_data['username']
                    full_name = user_data['full_name']
                else:
                    user_id = existing_user[0]
                    username = existing_user[1]
                    full_name = existing_user[2]
                
                print(f"Existing user logged in: {username}")
                return {
                    'id': user_id,
                    'username': username,
                    'email': email,
                    'full_name': full_name,
                    'picture': picture,
                    'is_new': False
                }
            else:
                # Create new user
                username = email.split('@')[0]  # Use email prefix as username
                password = "google_oauth_user"  # Placeholder password
                
                # Ensure unique username
                counter = 1
                original_username = username
                while True:
                    check_username_query = '''
                        SELECT id FROM users WHERE username = %s
                    ''' if not hasattr(connection, 'row_factory') else '''
                        SELECT id FROM users WHERE username = ?
                    '''
                    
                    cursor.execute(check_username_query, (username,))
                    if cursor.fetchone() is None:
                        break
                    username = f"{original_username}{counter}"
                    counter += 1
                
                # Insert new user
                insert_query = '''
                    INSERT INTO users (username, email, password_hash, full_name)
                    VALUES (%s, %s, %s, %s)
                ''' if not hasattr(connection, 'row_factory') else '''
                    INSERT INTO users (username, email, password_hash, full_name)
                    VALUES (?, ?, ?, ?)
                '''
                
                cursor.execute(insert_query, (username, email, db.hash_password(password), name))
                connection.commit()
                
                print(f"New user created: {username}")
                return {
                    'id': cursor.lastrowid if not hasattr(connection, 'row_factory') else cursor.lastrowid,
                    'username': username,
                    'email': email,
                    'full_name': name,
                    'picture': picture,
                    'is_new': True
                }
                
        except Exception as e:
            print(f"Error creating/updating user: {e}")
            return None
        finally:
            if hasattr(connection, 'close'):
                connection.close()

# Global OAuth instance
oauth = GoogleOAuth()
