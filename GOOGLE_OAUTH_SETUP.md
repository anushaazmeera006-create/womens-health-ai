# Google OAuth Setup Guide

## Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Go to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth 2.0 Client IDs"
5. Select "Web application"
6. Add authorized redirect URI: `http://127.0.0.1:5000/login/google/callback`
7. Copy the Client ID and Client Secret

## Step 2: Set Environment Variables

Add these to your system environment variables or set them in your app:

```bash
export GOOGLE_CLIENT_ID="your_client_id_here"
export GOOGLE_CLIENT_SECRET="your_client_secret_here"
```

Or update the values in `google_oauth.py`:
```python
GOOGLE_CLIENT_ID = "your_client_id_here"
GOOGLE_CLIENT_SECRET = "your_client_secret_here"
```

## Step 3: Test the Integration

1. Restart your Flask application
2. Go to http://127.0.0.1:5000/signup or http://127.0.0.1:5000/login
3. Click "Sign up with Google" or "Sign in with Google"
4. Complete the Google authentication flow
5. You should be redirected back to your app's dashboard

## Features Added

- Google OAuth login/signup buttons
- Automatic user creation from Google profile
- Profile picture and name import
- Secure OAuth flow with state verification
- Database integration for Google users

## Notes

- Google OAuth requires HTTPS for production
- For development, localhost is allowed
- Users can sign up with Google or traditional email/password
- Google users get automatic profile picture and name import
