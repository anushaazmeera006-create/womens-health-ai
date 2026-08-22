import os
from datetime import datetime, timedelta

from flask import Flask, redirect, render_template, request, session, url_for, jsonify

from cycle_predictor import CyclePredictor
from risk_model import HealthRiskModel
from symptom_cluster import SymptomClusterer
from database import db


app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY", "period-tracker-dev-key")

predictor = CyclePredictor()
clusterer = SymptomClusterer()
clusterer.fit()
try:
    risk_model = HealthRiskModel()
except Exception:
    risk_model = None


# DISABLED: Authentication bypass - removed for proper authentication
# @app.before_request
# def set_default_user():
#     """Set default user_id if not in session (bypasses authentication)"""
#     if "user_id" not in session:
#         session["user_id"] = 1  # Default user ID
#         session["user_name"] = "User"
#         session["logged_in"] = True  # Set as logged in by default


def get_local_date():
    return datetime.now().astimezone().date()


def get_default_period_dates():
    today = get_local_date()
    return [
        (today - timedelta(days=160)).isoformat(),
        (today - timedelta(days=132)).isoformat(),
        (today - timedelta(days=102)).isoformat(),
        (today - timedelta(days=73)).isoformat(),
        (today - timedelta(days=42)).isoformat(),
        (today - timedelta(days=14)).isoformat(),
    ]


def ensure_state():
    if "period_dates" not in session:
        session["period_dates"] = get_default_period_dates()
    if "symptom_logs" not in session:
        session["symptom_logs"] = []
    if "period_length_days" not in session:
        session["period_length_days"] = 5


def set_message(msg_type, text):
    session["message"] = {"type": msg_type, "text": text}


def pop_message():
    return session.pop("message", None)


def parsed_dates():
    dates = []
    for item in session.get("period_dates", []):
        try:
            dates.append(datetime.fromisoformat(item).date())
        except ValueError:
            continue
    return sorted(dates)


def predict_cycle_phase(period_dates, current_date):
    """Predict current cycle phase based on period dates"""
    if len(period_dates) < 2:
        return "Follicular"  # Default phase
    
    # Sort dates and find most recent period
    dates = sorted(period_dates)
    most_recent = None
    for date in reversed(dates):
        if date <= current_date:
            most_recent = date
            break
    
    if not most_recent:
        return "Follicular"
    
    # Calculate days since last period
    days_since_period = (current_date - most_recent).days
    
    # Calculate average cycle length
    cycle_lengths = []
    for i in range(1, len(dates)):
        length = (dates[i] - dates[i-1]).days
        cycle_lengths.append(length)
    
    avg_cycle = sum(cycle_lengths) / len(cycle_lengths) if cycle_lengths else 28
    
    # Determine phase based on days since last period
    period_length = session.get("period_length_days", 5)
    
    if days_since_period <= period_length:
        return "Menstrual"
    elif days_since_period <= period_length + 7:
        return "Follicular"
    elif days_since_period <= period_length + 14:
        return "Ovulation"
    else:
        return "Luteal"


def get_cycle_assessment_data(period_dates):
    """Analyze cycle data and return assessment values for risk questionnaire"""
    if len(period_dates) < 2:
        return {
            "cycle_regularity": "",
            "cycle_length_variation": "",
            "menstrual_flow": ""
        }
    
    # Convert to datetime objects and sort
    dates = [datetime.strptime(d, "%Y-%m-%d").date() for d in period_dates]
    dates = sorted(dates)
    
    # Calculate cycle lengths
    cycle_lengths = []
    for i in range(1, len(dates)):
        cycle_length = (dates[i] - dates[i-1]).days
        cycle_lengths.append(cycle_length)
    
    if not cycle_lengths:
        return {
            "cycle_regularity": "",
            "cycle_length_variation": "",
            "menstrual_flow": ""
        }
    
    # Calculate average cycle length
    avg_cycle = sum(cycle_lengths) / len(cycle_lengths)
    
    # Determine cycle regularity (0-3 scale)
    if len(cycle_lengths) >= 3:
        cycle_variation = max(cycle_lengths) - min(cycle_lengths)
        if cycle_variation <= 3:
            cycle_regularity = "0"  # Very regular
        elif cycle_variation <= 7:
            cycle_regularity = "1"  # Mostly regular
        elif cycle_variation <= 14:
            cycle_regularity = "2"  # Irregular
        else:
            cycle_regularity = "3"  # Very irregular
    else:
        cycle_regularity = "1"  # Default to mostly regular if insufficient data
    
    # Determine cycle length variation
    if avg_cycle >= 26 and avg_cycle <= 32:
        cycle_length_variation = "0"  # Normal range
    elif avg_cycle >= 24 and avg_cycle <= 35:
        cycle_length_variation = "1"  # Slight variation
    elif avg_cycle >= 21 and avg_cycle <= 40:
        cycle_length_variation = "2"  # Moderate variation
    else:
        cycle_length_variation = "3"  # Significant variation
    
    # Get period length from session (default to normal)
    period_length = session.get("period_length_days", 5)
    if period_length <= 4:
        menstrual_flow = "1"  # Light
    elif period_length <= 7:
        menstrual_flow = "0"  # Normal
    else:
        menstrual_flow = "2"  # Heavy
    
    return {
        "cycle_regularity": cycle_regularity,
        "cycle_length_variation": cycle_length_variation,
        "menstrual_flow": menstrual_flow
    }


def get_dashboard_data():
    from datetime import datetime, timedelta
    
    # Get user's period dates from database (same as cycle timeline)
    user_period_dates = db.get_user_period_dates(session.get("user_id", 1))
    
    # Get actual logged period dates from symptom logs (same as cycle timeline)
    logs = db.get_user_symptom_logs(session.get("user_id", 1))
    
    logged_period_dates = []
    for log in logs:
        if log.get('had_period') == 'Yes':
            log_date = log.get('selected_date')
            if hasattr(log_date, 'strftime'):
                date_str = log_date.strftime('%Y-%m-%d')
            else:
                date_str = str(log_date)
            logged_period_dates.append(date_str)
    
    # Filter to keep only the first day of each period (same as cycle timeline)
    logged_period_dates.sort()
    filtered_logged_dates = []
    prev_date = None
    
    for date_str in logged_period_dates:
        current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # If this is the first period date or it's not consecutive with previous
        if prev_date is None or (current_date - prev_date).days > 1:
            filtered_logged_dates.append(date_str)
            prev_date = current_date
        # Skip consecutive days (2nd, 3rd, 4th, 5th day of same period)
    
    logged_period_dates = filtered_logged_dates
    
    # Combine both sources and ensure all are strings (same as cycle timeline)
    all_period_dates = list(set(user_period_dates + logged_period_dates))
    
    # Convert all dates to strings with better type checking
    string_dates = []
    for date_obj in all_period_dates:
        if isinstance(date_obj, str):
            string_dates.append(date_obj)
        elif hasattr(date_obj, 'strftime'):  # datetime.date or datetime.datetime
            string_dates.append(date_obj.strftime('%Y-%m-%d'))
        else:
            string_dates.append(str(date_obj))
    
    all_period_dates = string_dates
    all_period_dates.sort()  # Sort by date
    
    # Convert to datetime objects for calculations
    dates = []
    for date_str in all_period_dates:
        try:
            dates.append(datetime.strptime(date_str, '%Y-%m-%d').date())
        except ValueError:
            continue
    
    # Calculate cycle lengths with error handling (same as cycle timeline)
    cycle_lengths = []
    if len(all_period_dates) > 1:
        for i in range(1, len(all_period_dates)):
            try:
                prev_date_str = all_period_dates[i-1]
                curr_date_str = all_period_dates[i]
                
                # Ensure we're working with strings
                if not isinstance(prev_date_str, str) or not isinstance(curr_date_str, str):
                    continue
                    
                prev_date = datetime.strptime(prev_date_str, '%Y-%m-%d').date()
                curr_date = datetime.strptime(curr_date_str, '%Y-%m-%d').date()
                cycle_length = (curr_date - prev_date).days
                cycle_lengths.append(cycle_length)
            except (ValueError, TypeError) as e:
                # Skip invalid dates
                continue
    
    # Calculate real predictions from user data (same as cycle timeline)
    avg_cycle = 28  # default
    predicted_length = 28  # default
    next_period_date = None
    next_period_label = "Unknown"
    
    if cycle_lengths:
        # Calculate average cycle length
        avg_cycle = round(sum(cycle_lengths) / len(cycle_lengths))
        
        # Predict next cycle length (use most recent cycle length or average)
        predicted_length = cycle_lengths[-1] if cycle_lengths else avg_cycle
        
        # Calculate next period date
        if all_period_dates:
            last_period = datetime.strptime(all_period_dates[-1], '%Y-%m-%d').date()
            next_period_date = last_period + timedelta(days=predicted_length)
            
            # Determine if next period is today, past, or future
            today = datetime.now().date()
            if next_period_date == today:
                next_period_label = "Today"
            elif next_period_date < today:
                days_late = (today - next_period_date).days
                next_period_label = f"Your period is {days_late} days late"
            else:
                days_until = (next_period_date - today).days
                if days_until == 1:
                    next_period_label = "Tomorrow"
                else:
                    next_period_label = f"In {days_until} days"
    
    # Predict cycle phase for today
    predicted_phase = predict_cycle_phase(dates, get_local_date())
    
    return {
        "avg_cycle": avg_cycle,
        "predicted_length": predicted_length,
        "next_period_label": next_period_label,
        "next_date": next_period_date.isoformat() if next_period_date else "Unknown",
        "period_dates": all_period_dates,
        "cycle_lengths": cycle_lengths,
        "predicted_phase": predicted_phase,
        "logs_count": len(session.get("symptom_logs", [])),
        "latest_log": session.get("symptom_logs", [])[-1] if session.get("symptom_logs") else None,
        "period_length_days": session.get("period_length_days", 5),
    }


def is_logged_in():
    return bool(session.get("logged_in"))


def require_login():
    if not is_logged_in():
        return redirect(url_for("login"))
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password:
            return render_template("login.html", error="Please enter username and password.")
        
        user = db.authenticate_user(username, password)
        if user:
            session["logged_in"] = True
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["user_name"] = user.get("full_name", user["username"])
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password.")
    
    return render_template("login.html", error=None)


@app.route("/check-username", methods=["POST"])
def check_username():
    """Check if username is available"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if len(username) < 3:
            return jsonify({'available': False, 'message': 'Username too short'})
        
        connection = db._get_connection()
        cursor = connection.cursor()
        
        check_query = '''
            SELECT username FROM users 
            WHERE username = %s
        ''' if not hasattr(connection, 'row_factory') else '''
            SELECT username FROM users 
            WHERE username = ?
        '''
        
        cursor.execute(check_query, (username,))
        existing_user = cursor.fetchone()
        
        connection.close()
        
        if existing_user:
            return jsonify({'available': False})
        else:
            return jsonify({'available': True})
            
    except Exception as e:
        print(f"Error checking username: {e}")
        return jsonify({'available': False, 'message': 'Error checking username'})


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        full_name = request.form.get("full_name", "").strip()
        mobile_number = request.form.get("mobile_number", "").strip()
        
        # Validation
        if not username or not password or not full_name or not mobile_number:
            return render_template("signup.html", error="All required fields must be filled.")
        
        if len(username) < 3:
            return render_template("signup.html", error="Username must be at least 3 characters long.")
        
        if password != confirm_password:
            return render_template("signup.html", error="Passwords do not match.")
        
        if len(password) < 6:
            return render_template("signup.html", error="Password must be at least 6 characters long.")
        
        if len(mobile_number) < 10:
            return render_template("signup.html", error="Please enter a valid mobile number.")
        
        # Create user
        try:
            success = db.create_user_new(
                username=username,
                password=password,
                full_name=full_name,
                mobile_number=mobile_number
            )
            
            if success:
                # Auto-login after signup
                user = db.authenticate_user(username, password)
                if user:
                    session["logged_in"] = True
                    session["user_id"] = user["id"]
                    session["username"] = user["username"]
                    session["user_name"] = user.get("full_name", user["username"])
                    return redirect(url_for("dashboard"))
                else:
                    return render_template("login.html", error="Account created successfully! Please sign in.")
            else:
                return render_template("signup.html", error="Username already exists. Please try another.")
        except Exception as e:
            print(f"Signup error: {e}")
            return render_template("signup.html", error="An error occurred during account creation. Please try again.")
    
    return render_template("signup.html", error=None)


# DISABLED: Google OAuth routes - commented out for future restoration
# @app.route("/login/google")
# def google_login():
#     """Initiate Google OAuth login"""
#     redirect_uri = url_for('google_callback', _external=True)
#     flow = oauth.get_flow(redirect_uri)
#     
#     # Generate authorization URL
#     authorization_url, state = flow.authorization_url(
#         access_type='offline',
#         include_granted_scopes='true',
#         prompt='consent'
#     )
#     
#     # Store state in session for security
#     session['google_oauth_state'] = state
#     
#     return redirect(authorization_url)


# @app.route("/login/google/callback")
# def google_callback():
#     """Handle Google OAuth callback"""
#     # Verify state to prevent CSRF attacks
#     state = session.pop('google_oauth_state', None)
#     if state is None or state != request.args.get('state'):
#         return render_template("login.html", error="Invalid OAuth state. Please try again.")
#     
#     redirect_uri = url_for('google_callback', _external=True)
#     flow = oauth.get_flow(redirect_uri)
#     
#     try:
#         # Exchange authorization code for access token
#         flow.fetch_token(authorization_response=request.url)
#         credentials = flow.credentials
#         
#         # Get user information
#         user_info = oauth.get_user_info(credentials)
#         
#         if user_info:
#             # Create or update user in database
#             user_data = oauth.create_or_update_user(user_info)
#             
#             if user_data:
#                 # Log user in
#                 session["logged_in"] = True
#                 session["user_id"] = user_data['id']
#                 session["username"] = user_data['username']
#                 session["user_name"] = user_data.get('full_name', user_data['username'])
#                 session["google_user"] = True
#                 session["user_picture"] = user_data.get('picture', '')
#                 
#                 if user_data['is_new']:
#                     set_message("success", f"Welcome {user_data['full_name']}! Your Google account has been linked successfully.")
#                 else:
#                     set_message("success", f"Welcome back {user_data['full_name']}!")
#                 
#                 return redirect(url_for("dashboard"))
#             else:
#                 return render_template("login.html", error="Failed to create user account. Please try again.")
#         else:
#             return render_template("login.html", error="Failed to get user information from Google.")
#             
#     except Exception as e:
#         print(f"Google OAuth error: {e}")
#         return render_template("login.html", error="Authentication failed. Please try again.")


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
def home():
    if not is_logged_in():
        return redirect(url_for("login"))
    
    return redirect(url_for("dashboard"))


@app.get("/dashboard")
def dashboard():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    
    data = get_dashboard_data()
    
    # Get history data for dashboard
    logs = db.get_user_symptom_logs(session["user_id"])
    history_summary = {
        'total_logs': len(logs),
        'current_streak': calculate_current_streak(logs),
        'period_days': sum(1 for log in logs if log.get('had_period') == 'Yes'),
        'avg_pain_level': sum(log.get('pain_level', 0) for log in logs) / len(logs) if logs else 0
    }
    recent_logs = logs[:5] if logs else []
    
    message = pop_message()
    return render_template(
        "dashboard.html",
        data=data,
        history_summary=history_summary,
        recent_logs=recent_logs,
        message=message,
        active_page="dashboard",
        user_name=session.get("user_name", "User"),
    )


@app.route("/cycle", methods=["GET", "POST"])
def cycle():
    from datetime import datetime, timedelta
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    
    if request.method == "POST":
        new_date = request.form.get("period_date", "").strip()
        period_length = request.form.get("period_length_days", "5").strip()
        try:
            parsed = datetime.fromisoformat(new_date).date().isoformat()
            period_length_days = max(1, min(15, int(period_length)))
        except ValueError:
            set_message("error", "Invalid date format.")
            return redirect(url_for("cycle"))

        # Save to database
        success = db.save_period_date(session["user_id"], parsed, period_length_days)
        if success:
            set_message("success", "Cycle details saved. Continue with daily check.")
            return redirect(url_for("symptoms", selected_date=parsed))
        else:
            set_message("error", "Failed to save period date to database.")

    # Force fresh data by adding small delay to ensure database operations complete
    import time
    time.sleep(0.1)
    
    # Get user's period dates from database (both manual and logged)
    user_period_dates = db.get_user_period_dates(session["user_id"])
    print(f"CYCLE DEBUG: User manual period dates: {user_period_dates}")
    
    # Get actual logged period dates from symptom logs
    logs = db.get_user_symptom_logs(session["user_id"])
    print(f"CYCLE DEBUG: Total logs found: {len(logs)}")
    
    logged_period_dates = []
    for log in logs:
        if log.get('had_period') == 'Yes':
            log_date = log.get('selected_date')
            if hasattr(log_date, 'strftime'):
                date_str = log_date.strftime('%Y-%m-%d')
            else:
                date_str = str(log_date)
            logged_period_dates.append(date_str)
    
    print(f"CYCLE DEBUG: Menstrual logs found: {logged_period_dates}")
    
    # Filter to keep only the first day of each period
    # Sort the dates first
    logged_period_dates.sort()
    filtered_logged_dates = []
    prev_date = None
    
    for date_str in logged_period_dates:
        current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # If this is the first period date or it's not consecutive with previous
        if prev_date is None or (current_date - prev_date).days > 1:
            filtered_logged_dates.append(date_str)
            prev_date = current_date
        # Skip consecutive days (2nd, 3rd, 4th, 5th day of same period)
    
    logged_period_dates = filtered_logged_dates
    
    # Combine both sources and ensure all are strings
    all_period_dates = list(set(user_period_dates + logged_period_dates))
    
    # Convert all dates to strings with better type checking
    string_dates = []
    for date_obj in all_period_dates:
        if isinstance(date_obj, str):
            string_dates.append(date_obj)
        elif hasattr(date_obj, 'strftime'):  # datetime.date or datetime.datetime
            string_dates.append(date_obj.strftime('%Y-%m-%d'))
        else:
            string_dates.append(str(date_obj))
    
    all_period_dates = string_dates
    all_period_dates.sort()  # Sort by date
    
    print(f"CYCLE DEBUG: Final period dates for timeline: {all_period_dates}")
    
    # Calculate cycle lengths with error handling
    cycle_lengths = []
    if len(all_period_dates) > 1:
        for i in range(1, len(all_period_dates)):
            try:
                prev_date_str = all_period_dates[i-1]
                curr_date_str = all_period_dates[i]
                
                # Ensure we're working with strings
                if not isinstance(prev_date_str, str) or not isinstance(curr_date_str, str):
                    continue
                    
                prev_date = datetime.strptime(prev_date_str, '%Y-%m-%d').date()
                curr_date = datetime.strptime(curr_date_str, '%Y-%m-%d').date()
                cycle_length = (curr_date - prev_date).days
                cycle_lengths.append(cycle_length)
            except (ValueError, TypeError) as e:
                # Skip invalid dates
                continue
    
    # Calculate real predictions from user data
    avg_cycle = 28  # default
    predicted_length = 28  # default
    next_period_date = None
    next_period_label = "Unknown"
    
    if cycle_lengths:
        # Calculate average cycle length
        avg_cycle = round(sum(cycle_lengths) / len(cycle_lengths))
        
        # Predict next cycle length (use most recent cycle length or average)
        predicted_length = cycle_lengths[-1] if cycle_lengths else avg_cycle
        
        # Calculate next period date
        if all_period_dates:
            last_period = datetime.strptime(all_period_dates[-1], '%Y-%m-%d').date()
            next_period_date = last_period + timedelta(days=predicted_length)
            
            # Determine if next period is today, past, or future
            today = datetime.now().date()
            if next_period_date == today:
                next_period_label = "Today"
            elif next_period_date < today:
                days_late = (today - next_period_date).days
                next_period_label = f"Your period is {days_late} days late"
            else:
                days_until = (next_period_date - today).days
                if days_until == 1:
                    next_period_label = "Tomorrow"
                else:
                    next_period_label = f"In {days_until} days"
    
    data = get_dashboard_data()
    data["period_dates"] = all_period_dates
    data["logged_period_dates"] = logged_period_dates
    data["manual_period_dates"] = user_period_dates
    data["cycle_lengths"] = cycle_lengths
    data["avg_cycle"] = avg_cycle
    data["predicted_length"] = predicted_length
    data["next_date"] = next_period_date.strftime('%Y-%m-%d') if next_period_date else "Unknown"
    data["next_period_label"] = next_period_label
    
    message = pop_message()
    return render_template(
        "cycle.html",
        data=data,
        message=message,
        active_page="cycle",
        user_name=session.get("user_name", "User"),
    )


@app.route("/edit_date", methods=["POST"])
def edit_date():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    
    original_date = request.form.get("original_date")
    new_date = request.form.get("new_date")
    new_length = request.form.get("new_length")
    
    if not original_date or not new_date or not new_length:
        set_message("error", "All fields are required.")
        return redirect(url_for("cycle"))
    
    try:
        parsed_new = datetime.strptime(new_date, "%Y-%m-%d").date()
        parsed_original = datetime.strptime(original_date, "%Y-%m-%d").date()
        
        # Validate new date is not in future
        if parsed_new > datetime.now().date():
            set_message("error", "Date cannot be in the future.")
            return redirect(url_for("cycle"))
        
        # Update period dates
        period_dates = set(session.get("period_dates", []))
        if original_date in period_dates:
            period_dates.remove(original_date)
        period_dates.add(new_date)
        session["period_dates"] = sorted(period_dates)
        
        # Update period length for the new date
        session["period_length_days"] = max(1, min(15, int(new_length)))
        
        set_message("success", "Period date updated successfully.")
        return redirect(url_for("cycle"))
        
    except ValueError:
        set_message("error", "Invalid date format.")
        return redirect(url_for("cycle"))


@app.route("/delete_date", methods=["POST"])
def delete_date():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    
    date_to_delete = request.form.get("date")
    
    if not date_to_delete:
        set_message("error", "No date specified.")
        return redirect(url_for("cycle"))
    
    deleted = False
    
    # Try to delete from manual period dates in database
    try:
        success = db.delete_period_date(session["user_id"], date_to_delete)
        if success:
            deleted = True
            set_message("success", "Period date deleted successfully.")
    except:
        pass  # Method might not exist, continue with other deletion methods
    
    # Try to delete from symptom logs (menstrual logs)
    if not deleted:
        try:
            success = db.delete_symptom_log(session["user_id"], date_to_delete)
            if success:
                deleted = True
                set_message("success", "Menstrual log deleted successfully.")
        except:
            pass
    
    # Also try to remove from session as fallback
    if not deleted:
        period_dates = set(session.get("period_dates", []))
        if date_to_delete in period_dates:
            period_dates.remove(date_to_delete)
            session["period_dates"] = sorted(period_dates)
            deleted = True
            set_message("success", "Period date deleted successfully.")
    
    if not deleted:
        set_message("error", "Date not found.")
    
    # Add cache-busting parameter to force page refresh
    import time
    return redirect(url_for("cycle") + f"?t={int(time.time())}")


@app.route("/symptoms", methods=["GET", "POST"])
def symptoms():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    selected_date = request.args.get("selected_date", get_local_date().isoformat())

    if request.method == "POST":
        selected_symptoms = request.form.getlist("symptoms")
        mood_state = request.form.get("mood_state", "")
        other_symptom = request.form.get("other_symptom", "").strip()
        cycle_phase = request.form.get("cycle_phase", "Follicular")
        had_period = request.form.get("had_period", "No")

        # Auto-detect cycle phase based on period status and date
        if had_period == "Yes":
            auto_phase = "Menstrual"
        else:
            # Simple phase detection based on symptoms (can be enhanced later)
            if any(symptom in selected_symptoms for symptom in ["Breast tenderness", "Bloating", "Food cravings"]):
                auto_phase = "Luteal"
            elif "Energy level changes" in selected_symptoms or "Headaches" in selected_symptoms:
                auto_phase = "Ovulation"
            else:
                auto_phase = "Follicular"
        
        log = {
            "selected_date": request.form.get("selected_date", selected_date),
            "had_period": had_period,
            "cycle_phase": auto_phase,
            "symptoms_selected": selected_symptoms,
            "other_symptom": other_symptom,
            "mood_state": mood_state,
            "cramps": ("Period Cramps" in selected_symptoms),
            "fatigue": ("Fatigue" in selected_symptoms),
            "nausea": ("Nausea" in selected_symptoms),
            "mood_swings": ("Mood swings" in selected_symptoms or mood_state in ("Anxious/Nervous", "Irritated")),
            "acne": ("Acne" in selected_symptoms),
            "back_pain": ("Body pain" in selected_symptoms),
            "flow_intensity": int(request.form.get("flow_intensity", 2)),
            "pain_level": int(request.form.get("pain_level", 2)),
        }

        # Save to database
        try:
            print(f"SYMPTOMS DEBUG: Saving log - had_period: {had_period}, flow_intensity: {log.get('flow_intensity')}, pain_level: {log.get('pain_level')}")
            cluster = clusterer.predict_day(log)
            log["cluster_result"] = f"{cluster['emoji']} {cluster['name']}"
            
            success = db.save_symptom_log(session["user_id"], log)
            print(f"SYMPTOMS DEBUG: Database save result: {success}")
            if success:
                set_message("success", f"{cluster['emoji']} {cluster['name']} day logged successfully.")
            else:
                set_message("error", "Failed to save symptom log to database.")
        except Exception as exc:
            print(f"SYMPTOMS DEBUG: Exception during save: {exc}")
            set_message("error", f"Clustering failed: {exc}")
        
        return redirect(url_for("symptoms"))

    # Get user's symptom logs from database
    user_logs = db.get_user_symptom_logs(session["user_id"], limit=5)
    latest_log = user_logs[0] if user_logs else None
    
    data = get_dashboard_data()
    data["latest_log"] = latest_log
    data["logs_count"] = len(user_logs)
    
    message = pop_message()
    return render_template(
        "symptoms.html",
        data=data,
        message=message,
        active_page="symptoms",
        user_name=session.get("user_name", "User"),
    )


@app.post("/delete_log")
def delete_log():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    
    selected_date = request.form.get("selected_date")
    
    if selected_date:
        success = db.delete_symptom_log(session["user_id"], selected_date)
        if success:
            set_message("success", f"Log for {selected_date} deleted successfully.")
        else:
            set_message("error", f"Failed to delete log for {selected_date}.")
    else:
        set_message("error", "No date provided for deletion.")
    
    return redirect(url_for("history"))


@app.get("/history")
def history():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    
    try:
        # Get user's symptom logs
        logs = db.get_user_symptom_logs(session["user_id"])
        
        # Sort logs by date (most recent first)
        logs.sort(key=lambda x: x.get('selected_date'), reverse=True)
        
        # Calculate summary statistics
        summary = {
            'total_logs': len(logs),
            'current_streak': calculate_current_streak(logs),
            'period_days': sum(1 for log in logs if log.get('had_period') == 'Yes'),
            'avg_pain_level': sum(log.get('pain_level', 0) for log in logs) / len(logs) if logs else 0
        }
        
        # Get recent logs (last 10)
        recent_logs = logs[:10] if logs else []
        
        # Calculate pattern insights if enough data
        pattern_insights = None
        if len(logs) >= 5:
            pattern_insights = calculate_pattern_insights(logs)
        
        message = pop_message()
        return render_template(
            "history.html",
            summary=summary,
            recent_logs=recent_logs,
            pattern_insights=pattern_insights,
            message=message,
            active_page="history",
            user_name=session.get("user_name", "User"),
        )
    except Exception as e:
        print(f"History page error: {e}")
        import traceback
        traceback.print_exc()
        return f"Error loading history: {str(e)}", 500


def calculate_current_streak(logs):
    """Calculate current consecutive logging streak"""
    if not logs:
        return 0
    
    from datetime import datetime, date, timedelta
    
    streak = 0
    today = date.today()
    
    # Check if we have a log for today
    has_today = False
    for log in logs:
        log_date = log.get('selected_date')
        if isinstance(log_date, str):
            log_date = datetime.strptime(log_date, '%Y-%m-%d').date()
        
        if log_date == today:
            has_today = True
            break
    
    if not has_today:
        return 0
    
    # Count consecutive days starting from today
    for i in range(len(logs)):
        expected_date = today - timedelta(days=i)
        
        found = False
        for log in logs:
            log_date = log.get('selected_date')
            if isinstance(log_date, str):
                log_date = datetime.strptime(log_date, '%Y-%m-%d').date()
            
            if log_date == expected_date:
                found = True
                break
        
        if found:
            streak += 1
        else:
            break
    
    return streak


def calculate_pattern_insights(logs):
    """Calculate pattern insights from logs"""
    import json
    from collections import Counter
    
    insights = {}
    
    # Most common symptoms
    all_symptoms = []
    for log in logs:
        symptoms = log.get('symptoms_selected', '')
        if isinstance(symptoms, str):
            symptoms = json.loads(symptoms) if symptoms.startswith('[') else symptoms.split(',')
        elif isinstance(symptoms, list):
            symptoms = symptoms
        all_symptoms.extend([s.strip() for s in symptoms if s.strip()])
    
    symptom_counts = Counter(all_symptoms)
    insights['common_symptoms'] = [
        {'symptom': symptom, 'count': count} 
        for symptom, count in symptom_counts.most_common(10)
    ]
    
    # Mood distribution
    moods = [log.get('mood_state', '') for log in logs if log.get('mood_state')]
    mood_counts = Counter(moods)
    total_moods = len(moods)
    insights['mood_distribution'] = [
        (mood, (count / total_moods) * 100) 
        for mood, count in mood_counts.items()
    ]
    
    # Cycle phase breakdown
    phases = [log.get('cycle_phase', '') for log in logs if log.get('cycle_phase')]
    phase_counts = Counter(phases)
    insights['cycle_phases'] = list(phase_counts.items())
    
    # Pain trends
    pain_levels = [log.get('pain_level', 0) for log in logs if log.get('pain_level') is not None]
    insights['avg_pain'] = sum(pain_levels) / len(pain_levels) if pain_levels else 0
    insights['high_pain_days'] = len([p for p in pain_levels if p >= 4])
    insights['pain_free_days'] = len([p for p in pain_levels if p <= 1])
    
    return insights


@app.get("/patterns")
def patterns():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    
    # Get user's symptom logs from database
    logs = db.get_user_symptom_logs(session["user_id"])
    summary = None

    if len(logs) < 3:
        set_message("error", "Need at least 3 logs for pattern analysis. Keep logging your daily symptoms!")
    else:
        try:
            summary = clusterer.get_pattern_summary(logs)
        except Exception as exc:
            set_message("error", f"Pattern analysis failed: {exc}")

    data = get_dashboard_data()
    data["latest_log"] = logs[0] if logs else None
    data["logs_count"] = len(logs)
    data["logs"] = logs  # Add logs data for timeline graph
    
    message = pop_message()
    
    return render_template(
        "patterns.html",
        data=data,
        summary=summary,
        message=message,
        active_page="patterns",
        user_name=session.get("user_name", "User"),
    )


@app.route("/risk_results", methods=["GET", "POST"])
def risk_results():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    
    # Handle form submissions
    if request.method == "POST":
        if "reset_assessment" in request.form:
            # Clear PCOS assessment session
            if "pcos_assessment" in session:
                session.pop("pcos_assessment", None)
            session.modified = True
            return redirect(url_for("risk_pcos"))
        elif "start_new_assessment" in request.form:
            # Clear all assessment data and start fresh
            if "pcos_assessment" in session:
                session.pop("pcos_assessment", None)
            if "endometriosis_assessment" in session:
                session.pop("endometriosis_assessment", None)
            session.pop("health_result", None)
            session.modified = True
            return redirect(url_for("risk"))
    
    health_result = session.get("health_result")
    if not health_result:
        return redirect(url_for("risk"))
    
    data = get_dashboard_data()
    message = pop_message()
    
    return render_template(
        "risk_results.html",
        data=data,
        health_result=health_result,
        message=message,
        active_page="risk",
        user_name=session.get("user_name", "User"),
    )


def calculate_pcos_risk(assessment_data):
    """Calculate PCOS risk based on assessment data"""
    risk_score = 0
    max_score = 0
    risk_factors = []
    
    # Basic factors
    age = int(assessment_data.get('age', 25))
    weight = float(assessment_data.get('weight', 60))
    height = float(assessment_data.get('height', 160))
    
    # Calculate BMI
    if height > 0:
        bmi = weight / ((height / 100) ** 2)
        if bmi >= 30:
            risk_score += 15
            risk_factors.append({"name": "High BMI", "level": "High"})
        elif bmi >= 25:
            risk_score += 10
            risk_factors.append({"name": "Overweight", "level": "Medium"})
        max_score += 15
    
    # Hormonal symptoms
    hormonal_score = 0
    hormonal_factors = {
        'excess_hair_growth': int(assessment_data.get('excess_hair_growth', 0)),
        'hair_thinning': int(assessment_data.get('hair_thinning', 0)),
        'severe_acne': int(assessment_data.get('severe_acne', 0))
    }
    
    hormonal_score = sum(hormonal_factors.values())
    risk_score += hormonal_score * 5
    max_score += 15
    
    if hormonal_score >= 6:
        risk_factors.append({"name": "Significant Hormonal Symptoms", "level": "High"})
    elif hormonal_score >= 3:
        risk_factors.append({"name": "Moderate Hormonal Symptoms", "level": "Medium"})
    
    # Metabolic factors
    metabolic_score = 0
    metabolic_factors = {
        'rapid_weight_gain': int(assessment_data.get('rapid_weight_gain', 0)),
        'difficulty_losing_weight': int(assessment_data.get('difficulty_losing_weight', 0)),
        'skin_darkening': int(assessment_data.get('skin_darkening', 0)),
        'sugar_cravings': int(assessment_data.get('sugar_cravings', 0)),
        'fatigue_after_meals': int(assessment_data.get('fatigue_after_meals', 0))
    }
    
    metabolic_score = sum(metabolic_factors.values())
    risk_score += metabolic_score * 3
    max_score += 15
    
    if metabolic_score >= 9:
        risk_factors.append({"name": "Significant Metabolic Issues", "level": "High"})
    elif metabolic_score >= 5:
        risk_factors.append({"name": "Some Metabolic Issues", "level": "Medium"})
    
    # Lifestyle factors
    lifestyle_score = 0
    lifestyle_factors = {
        'fast_food_frequency': int(assessment_data.get('fast_food_frequency', 0)),
        'exercise_level': int(assessment_data.get('exercise_level', 0)),
        'sleep_quality': int(assessment_data.get('sleep_quality', 0))
    }
    
    lifestyle_score = sum(lifestyle_factors.values())
    risk_score += lifestyle_score * 2
    max_score += 6
    
    # Family history
    family_score = 0
    family_factors = {
        'family_pcos_mother': int(assessment_data.get('family_pcos_mother', 0)),
        'family_pcos_sister': int(assessment_data.get('family_pcos_sister', 0))
    }
    
    family_score = sum(family_factors.values())
    risk_score += family_score * 8
    max_score += 16
    
    if family_score >= 2:
        risk_factors.append({"name": "Family History", "level": "High"})
    elif family_score >= 1:
        risk_factors.append({"name": "Some Family History", "level": "Medium"})
    
    # Calculate final risk percentage
    risk_percentage = min(int((risk_score / max_score) * 100), 95)
    
    # Determine risk level
    if risk_percentage >= 70:
        risk_level = "High"
        findings = [
            "Multiple PCOS risk factors present",
            "Significant hormonal and metabolic symptoms",
            "Strong indication for medical evaluation"
        ]
        recommendations = [
            "Consult with a healthcare provider for PCOS evaluation",
            "Consider hormonal testing and ultrasound",
            "Discuss lifestyle modifications",
            "Monitor symptoms regularly"
        ]
    elif risk_percentage >= 40:
        risk_level = "Medium"
        findings = [
            "Some PCOS risk factors present",
            "Moderate symptoms",
            "Medical evaluation recommended"
        ]
        recommendations = [
            "Schedule check-up with healthcare provider",
            "Monitor symptoms",
            "Consider lifestyle changes",
            "Track menstrual cycles"
        ]
    else:
        risk_level = "Low"
        findings = [
            "Minimal PCOS risk factors",
            "Few symptoms present",
            "Continue monitoring"
        ]
        recommendations = [
            "Maintain healthy lifestyle",
            "Regular check-ups",
            "Monitor for new symptoms"
        ]
    
    return {
        "risk_percentage": risk_percentage,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "assessment_summary": findings,
        "recommendations": recommendations
    }




def get_pcos_questionnaire():
    """Get PCOS risk assessment questionnaire"""
    questionnaire_steps = [
        {
            "id": "age_basic",
            "title": "About You",
            "subtitle": "Let's get to know you better and calculate your BMI",
            "input_fields": [
                {
                    "id": "age",
                    "question": "How old are you?",
                    "type": "number",
                    "placeholder": "Enter your age",
                    "min": "10",
                    "max": "100"
                },
                {
                    "id": "weight",
                    "question": "What's your current weight? (kgs)",
                    "type": "number",
                    "placeholder": "Enter your weight in kgs",
                    "min": "30",
                    "max": "200"
                },
                {
                    "id": "height",
                    "question": "How tall are you? (cm)",
                    "type": "number",
                    "placeholder": "Enter your height in cm",
                    "min": "100",
                    "max": "220"
                }
            ]
        }
    ]
    
    questionnaire_steps.extend([
            {
                "id": "hormonal_symptoms",
            "title": "Your Body Changes",
            "subtitle": "Let's check for common PCOS signs",
            "questions": [
                {
                    "id": "excess_hair_growth",
                    "question": "Have you noticed unusual hair growth on your face, chest, or other body areas?",
                    "options": [
                        {"value": "0", "label": "No extra hair", "explanation": "This is normal for you"},
                        {"value": "1", "label": "A little extra hair", "explanation": "Slight increase in hair growth"},
                        {"value": "2", "label": "Quite a bit extra hair", "explanation": "Noticeable increase in hair growth"},
                        {"value": "3", "label": "A lot of extra hair", "explanation": "Significant increase in hair growth"}
                    ]
                },
                {
                    "id": "hair_thinning",
                    "question": "Are you experiencing hair thinning or hair loss, especially on your scalp?",
                    "options": [
                        {"value": "0", "label": "No hair loss", "explanation": "Your hair is normal and healthy"},
                        {"value": "1", "label": "A little thinning", "explanation": "Early signs of hair changes"},
                        {"value": "2", "label": "Noticeable thinning", "explanation": "Your hair is getting thinner over time"},
                        {"value": "3", "label": "A lot of thinning", "explanation": "Significant hair loss pattern"}
                    ]
                },
                {
                    "id": "severe_acne",
                    "question": "How often do you experience acne, pimples, or skin breakouts on your face or body?",
                    "options": [
                        {"value": "0", "label": "Clear or almost clear skin", "explanation": "Your skin is doing great"},
                        {"value": "1", "label": "Some pimples sometimes", "explanation": "Normal teenage/adult skin"},
                        {"value": "2", "label": "Frequent breakouts", "explanation": "Hormone-related skin issues"},
                        {"value": "3", "label": "Severe acne all the time", "explanation": "Significant hormone imbalance signs"}
                    ]
                }
            ]
        },
        {
            "id": "weight_metabolism",
            "title": "Your Weight Changes",
            "subtitle": "Let's understand your body's metabolism",
            "questions": [
                {
                    "id": "rapid_weight_gain",
                    "question": "Have you experienced rapid or unexplained weight gain in the past few months?",
                    "options": [
                        {"value": "0", "label": "No, my weight is stable", "explanation": "This is a healthy pattern"},
                        {"value": "1", "label": "Yes, a little bit (2-5 kgs)", "explanation": "Small changes in weight"},
                        {"value": "2", "label": "Yes, quite a bit (5-10 kgs)", "explanation": "Your metabolism may be slowing"},
                        {"value": "3", "label": "Yes, a lot (10+ kgs)", "explanation": "Your body is storing more fat"}
                    ]
                },
                {
                    "id": "difficulty_losing_weight",
                    "question": "Do you find it difficult to lose weight even with diet and exercise?",
                    "options": [
                        {"value": "0", "label": "No, I can lose weight normally", "explanation": "Your metabolism is working well"},
                        {"value": "1", "label": "A little harder than expected", "explanation": "Might be some resistance"},
                        {"value": "2", "label": "Much harder than it should be", "explanation": "Your body fights weight loss"},
                        {"value": "3", "label": "Almost impossible to lose weight", "explanation": "Your metabolism needs medical attention"}
                    ]
                }
            ]
        },
        {
            "id": "insulin_resistance",
            "title": "Your Blood Sugar Signs",
            "subtitle": "Let's check how your body handles sugar",
            "questions": [
                {
                    "id": "skin_darkening",
                    "question": "Have you noticed dark, velvety skin patches on your neck, armpits, groin, or under breasts?",
                    "options": [
                        {"value": "0", "label": "No dark patches", "explanation": "Your skin looks normal and healthy"},
                        {"value": "1", "label": "A few light patches", "explanation": "Early signs your body is struggling with sugar"},
                        {"value": "2", "label": "Noticeable dark patches", "explanation": "Your body has sugar processing issues"},
                        {"value": "3", "label": "Very dark, thick patches", "explanation": "Your body needs medical attention for sugar issues"}
                    ]
                },
                {
                    "id": "sugar_cravings",
                    "question": "How often do you experience strong cravings for sweets, sugar, or carbohydrates?",
                    "options": [
                        {"value": "0", "label": "Rarely or never", "explanation": "Your blood sugar is stable"},
                        {"value": "1", "label": "Sometimes", "explanation": "Mild blood sugar ups and downs"},
                        {"value": "2", "label": "Often", "explanation": "Your blood sugar goes up and down a lot"},
                        {"value": "3", "label": "All the time, can't stop thinking about sweets", "explanation": "Your body has trouble with blood sugar control"}
                    ]
                },
                {
                    "id": "fatigue_after_meals",
                    "question": "Do you feel extremely tired, sleepy, or need to rest within 1-2 hours after eating?",
                    "options": [
                        {"value": "0", "label": "No, I feel normal after eating", "explanation": "Your body handles food well"},
                        {"value": "1", "label": "Sometimes I get sleepy", "explanation": "Mild blood sugar spikes after meals"},
                        {"value": "2", "label": "Often I feel very tired", "explanation": "Your blood sugar goes up and down after eating"},
                        {"value": "3", "label": "Always feel like I need to nap after eating", "explanation": "Your body struggles with blood sugar after meals"}
                    ]
                }
            ]
        },
        {
            "id": "lifestyle_factors",
            "title": "Your Daily Habits",
            "subtitle": "Let's understand your lifestyle patterns",
            "questions": [
                {
                    "id": "fast_food_frequency",
                    "question": "How often do you eat processed foods, takeout, or fast food meals?",
                    "options": [
                        {"value": "0", "label": "Rarely or never", "explanation": "You eat mostly fresh, home-cooked food"},
                        {"value": "1", "label": "Sometimes (1-2 times a week)", "explanation": "You mix healthy and convenience foods"},
                        {"value": "2", "label": "Often (3-5 times a week)", "explanation": "You rely on convenience foods frequently"},
                        {"value": "3", "label": "Almost every day", "explanation": "You eat mostly processed foods"}
                    ]
                },
                {
                    "id": "exercise_level",
                    "question": "How often do you exercise, do physical activities, or move your body intentionally?",
                    "options": [
                        {"value": "0", "label": "Very active (3+ times a week)", "explanation": "Great for your hormones and health"},
                        {"value": "1", "label": "Sometimes active (1-2 times a week)", "explanation": "Good but could be more consistent"},
                        {"value": "2", "label": "A little active (rarely)", "explanation": "Your body needs more movement"},
                        {"value": "3", "label": "Not very active (mostly sitting)", "explanation": "Your body needs much more movement"}
                    ]
                },
                {
                    "id": "sleep_quality",
                    "question": "How many hours of quality sleep do you get each night and how refreshed do you feel?",
                    "options": [
                        {"value": "0", "label": "Great sleep (7-8 hours, wake up refreshed)", "explanation": "Your body gets the rest it needs"},
                        {"value": "1", "label": "Okay sleep (6-7 hours, sometimes wake up)", "explanation": "Your sleep could be better"},
                        {"value": "2", "label": "Poor sleep (5-6 hours, wake up tired)", "explanation": "Your body needs more quality sleep"},
                        {"value": "3", "label": "Very poor sleep (less than 5 hours)", "explanation": "Your body is not getting enough rest"}
                    ]
                }
            ]
        },
        {
            "id": "family_history",
            "title": "Your Family Health",
            "subtitle": "Let's understand your family background",
            "questions": [
                {
                    "id": "family_pcos_mother",
                    "question": "Has your mother ever been diagnosed with PCOS or had PCOS-like symptoms?",
                    "options": [
                        {"value": "0", "label": "No", "explanation": "No family risk from your mother"},
                        {"value": "1", "label": "Yes", "explanation": "PCOS can run in families"},
                        {"value": "2", "label": "I don't know", "explanation": "Family history is unclear"}
                    ]
                },
                {
                    "id": "family_pcos_sister",
                    "question": "Have any of your sisters been diagnosed with PCOS or shown PCOS symptoms?",
                    "options": [
                        {"value": "0", "label": "No", "explanation": "No family risk from your sisters"},
                        {"value": "1", "label": "Yes", "explanation": "PCOS can run in families"},
                        {"value": "2", "label": "I don't know", "explanation": "Family history is unclear"}
                    ]
                }
            ]
        }
    ])
    return questionnaire_steps

def get_endometriosis_questionnaire():
    """Get endometriosis risk assessment questionnaire"""
    questionnaire_steps = [
        {
            "id": "basic_info",
            "title": "About You",
            "subtitle": "Let's understand your basic health profile",
            "input_fields": [
                {
                    "id": "age",
                    "question": "How old are you?",
                    "type": "number",
                    "placeholder": "Enter your age",
                    "min": "10",
                    "max": "100"
                },
                {
                    "id": "pain_duration",
                    "question": "How long have you been experiencing pelvic pain?",
                    "type": "number",
                    "placeholder": "Years",
                    "min": "0",
                    "max": "50"
                }
            ]
        },
        {
            "id": "pain_patterns",
            "title": "Pain Patterns",
            "subtitle": "Let's assess your pain symptoms",
            "questions": [
                {
                    "id": "menstrual_pain",
                    "question": "How severe is your menstrual pain?",
                    "options": [
                        {"value": "0", "label": "No pain or mild discomfort", "explanation": "Normal menstrual cramps"},
                        {"value": "1", "label": "Moderate pain", "explanation": "Pain that affects daily activities"},
                        {"value": "2", "label": "Severe pain", "explanation": "Pain that prevents normal activities"},
                        {"value": "3", "label": "Debilitating pain", "explanation": "Pain requiring bed rest or emergency care"}
                    ]
                },
                {
                    "id": "chronic_pelvic_pain",
                    "question": "Do you experience pelvic pain outside of your period?",
                    "options": [
                        {"value": "0", "label": "No pelvic pain", "explanation": "No pain between periods"},
                        {"value": "1", "label": "Occasional pain", "explanation": "Sometimes have pelvic pain"},
                        {"value": "2", "label": "Frequent pain", "explanation": "Regular pelvic pain between periods"},
                        {"value": "3", "label": "Constant pain", "explanation": "Daily pelvic pain"}
                    ]
                },
                {
                    "id": "pain_during_intercourse",
                    "question": "Do you experience pain during or after sexual intercourse?",
                    "options": [
                        {"value": "0", "label": "No pain", "explanation": "Comfortable during intercourse"},
                        {"value": "1", "label": "Mild discomfort", "explanation": "Sometimes uncomfortable"},
                        {"value": "2", "label": "Moderate pain", "explanation": "Often painful during intercourse"},
                        {"value": "3", "label": "Severe pain", "explanation": "Always painful, may avoid intercourse"}
                    ]
                }
            ]
        },
        {
            "id": "menstrual_symptoms",
            "title": "Menstrual Symptoms",
            "subtitle": "Let's evaluate your period patterns",
            "questions": [
                {
                    "id": "heavy_bleeding",
                    "question": "How heavy is your menstrual bleeding?",
                    "options": [
                        {"value": "0", "label": "Normal flow", "explanation": "Regular bleeding pattern"},
                        {"value": "1", "label": "Somewhat heavy", "explanation": "Heavier than average but manageable"},
                        {"value": "2", "label": "Very heavy", "explanation": "Soaking through pads/tampons frequently"},
                        {"value": "3", "label": "Extremely heavy", "explanation": "Changing protection every hour or less"}
                    ]
                },
                {
                    "id": "irregular_periods",
                    "question": "How regular are your menstrual cycles?",
                    "options": [
                        {"value": "0", "label": "Very regular", "explanation": "Predictable cycles every 21-35 days"},
                        {"value": "1", "label": "Somewhat irregular", "explanation": "Occasional variation in timing"},
                        {"value": "2", "label": "Often irregular", "explanation": "Frequent variation in cycle length"},
                        {"value": "3", "label": "Very irregular", "explanation": "Unpredictable or missed periods"}
                    ]
                },
                {
                    "id": "period_length",
                    "question": "How long do your periods typically last?",
                    "options": [
                        {"value": "0", "label": "3-5 days", "explanation": "Normal duration"},
                        {"value": "1", "label": "6-7 days", "explanation": "Slightly longer than average"},
                        {"value": "2", "label": "8-10 days", "explanation": "Extended bleeding"},
                        {"value": "3", "label": "More than 10 days", "explanation": "Very prolonged bleeding"}
                    ]
                }
            ]
        },
        {
            "id": "other_symptoms",
            "title": "Other Symptoms",
            "subtitle": "Let's check for additional endometriosis signs",
            "questions": [
                {
                    "id": "bowel_symptoms",
                    "question": "Do you experience bowel pain or changes during your period?",
                    "options": [
                        {"value": "0", "label": "No bowel symptoms", "explanation": "Normal bowel function"},
                        {"value": "1", "label": "Mild discomfort", "explanation": "Slight bowel discomfort during period"},
                        {"value": "2", "label": "Moderate symptoms", "explanation": "Painful bowel movements, constipation/diarrhea"},
                        {"value": "3", "label": "Severe symptoms", "explanation": "Intense pain, significant bowel changes"}
                    ]
                },
                {
                    "id": "urinary_symptoms",
                    "question": "Do you experience urinary pain or frequency during your period?",
                    "options": [
                        {"value": "0", "label": "No urinary symptoms", "explanation": "Normal bladder function"},
                        {"value": "1", "label": "Mild discomfort", "explanation": "Slight bladder discomfort"},
                        {"value": "2", "label": "Moderate symptoms", "explanation": "Painful urination, increased frequency"},
                        {"value": "3", "label": "Severe symptoms", "explanation": "Intense pain, urgent/frequent urination"}
                    ]
                },
                {
                    "id": "fatigue",
                    "question": "How would you describe your energy levels?",
                    "options": [
                        {"value": "0", "label": "Good energy", "explanation": "Normal energy levels"},
                        {"value": "1", "label": "Mild fatigue", "explanation": "Sometimes tired but manageable"},
                        {"value": "2", "label": "Moderate fatigue", "explanation": "Often tired, affects daily life"},
                        {"value": "3", "label": "Severe fatigue", "explanation": "Constant exhaustion, debilitating"}
                    ]
                }
            ]
        },
        {
            "id": "quality_of_life",
            "title": "Quality of Life Impact",
            "subtitle": "Let's understand how symptoms affect your daily life",
            "questions": [
                {
                    "id": "work_impact",
                    "question": "How do your symptoms affect your work or school?",
                    "options": [
                        {"value": "0", "label": "No impact", "explanation": "Symptoms don't affect work/school"},
                        {"value": "1", "label": "Mild impact", "explanation": "Sometimes difficult but manageable"},
                        {"value": "2", "label": "Moderate impact", "explanation": "Often miss work/school or reduced performance"},
                        {"value": "3", "label": "Severe impact", "explanation": "Frequently unable to work/attend school"}
                    ]
                },
                {
                    "id": "social_impact",
                    "question": "How do your symptoms affect your social life?",
                    "options": [
                        {"value": "0", "label": "No impact", "explanation": "Social activities unaffected"},
                        {"value": "1", "label": "Mild impact", "explanation": "Sometimes cancel plans due to symptoms"},
                        {"value": "2", "label": "Moderate impact", "explanation": "Often avoid social activities"},
                        {"value": "3", "label": "Severe impact", "explanation": "Rarely participate in social activities"}
                    ]
                },
                {
                    "id": "mental_health",
                    "question": "How do your symptoms affect your mental health?",
                    "options": [
                        {"value": "0", "label": "No impact", "explanation": "Mental health unaffected"},
                        {"value": "1", "label": "Mild impact", "explanation": "Sometimes feel anxious or depressed"},
                        {"value": "2", "label": "Moderate impact", "explanation": "Often struggle with anxiety/depression"},
                        {"value": "3", "label": "Severe impact", "explanation": "Constant mental health struggles"}
                    ]
                }
            ]
        }
    ]
    return questionnaire_steps

def calculate_endometriosis_risk(assessment_data):
    """Calculate endometriosis risk based on assessment data"""
    risk_score = 0
    max_score = 0
    risk_factors = []
    
    # Pain symptoms (highest weight)
    pain_factors = {
        'menstrual_pain': int(assessment_data.get('menstrual_pain', 0)),
        'chronic_pelvic_pain': int(assessment_data.get('chronic_pelvic_pain', 0)),
        'pain_during_intercourse': int(assessment_data.get('pain_during_intercourse', 0))
    }
    
    pain_score = sum(pain_factors.values())
    max_score += 9  # 3 factors x max 3 points each
    risk_score += pain_score * 2  # Double weight for pain
    
    if pain_score >= 6:
        risk_factors.append({"name": "Severe Pain Symptoms", "level": "High"})
    elif pain_score >= 3:
        risk_factors.append({"name": "Moderate Pain Symptoms", "level": "Medium"})
    else:
        risk_factors.append({"name": "Mild Pain Symptoms", "level": "Low"})
    
    # Menstrual symptoms
    menstrual_factors = {
        'heavy_bleeding': int(assessment_data.get('heavy_bleeding', 0)),
        'irregular_periods': int(assessment_data.get('irregular_periods', 0)),
        'period_length': int(assessment_data.get('period_length', 0))
    }
    
    menstrual_score = sum(menstrual_factors.values())
    max_score += 9
    risk_score += menstrual_score
    
    if menstrual_score >= 6:
        risk_factors.append({"name": "Abnormal Menstrual Patterns", "level": "High"})
    elif menstrual_score >= 3:
        risk_factors.append({"name": "Some Menstrual Irregularities", "level": "Medium"})
    else:
        risk_factors.append({"name": "Normal Menstrual Patterns", "level": "Low"})
    
    # Other symptoms
    other_factors = {
        'bowel_symptoms': int(assessment_data.get('bowel_symptoms', 0)),
        'urinary_symptoms': int(assessment_data.get('urinary_symptoms', 0)),
        'fatigue': int(assessment_data.get('fatigue', 0))
    }
    
    other_score = sum(other_factors.values())
    max_score += 9
    risk_score += other_score
    
    if other_score >= 6:
        risk_factors.append({"name": "Significant Associated Symptoms", "level": "High"})
    elif other_score >= 3:
        risk_factors.append({"name": "Some Associated Symptoms", "level": "Medium"})
    else:
        risk_factors.append({"name": "Minimal Associated Symptoms", "level": "Low"})
    
    # Quality of life impact
    qol_factors = {
        'work_impact': int(assessment_data.get('work_impact', 0)),
        'social_impact': int(assessment_data.get('social_impact', 0)),
        'mental_health': int(assessment_data.get('mental_health', 0))
    }
    
    qol_score = sum(qol_factors.values())
    max_score += 9
    risk_score += qol_score
    
    if qol_score >= 6:
        risk_factors.append({"name": "Severe Quality of Life Impact", "level": "High"})
    elif qol_score >= 3:
        risk_factors.append({"name": "Moderate Quality of Life Impact", "level": "Medium"})
    else:
        risk_factors.append({"name": "Minimal Quality of Life Impact", "level": "Low"})
    
    # Calculate final risk percentage
    final_max_score = max_score * 2  # Account for pain weighting
    risk_percentage = min(int((risk_score / final_max_score) * 100), 95)
    
    # Determine risk level
    if risk_percentage >= 70:
        risk_level = "High"
        findings = [
            "Multiple severe endometriosis symptoms present",
            "Significant pain and menstrual abnormalities",
            "Major impact on daily functioning",
            "Strong clinical indication for endometriosis evaluation"
        ]
        recommendations = [
            "Seek immediate medical evaluation with a gynecologist",
            "Request referral to an endometriosis specialist",
            "Consider diagnostic imaging (ultrasound/MRI)",
            "Discuss pain management strategies with healthcare provider",
            "Document symptoms in a diary for medical appointments"
        ]
    elif risk_percentage >= 40:
        risk_level = "Medium"
        findings = [
            "Several endometriosis symptoms present",
            "Moderate pain and/or menstrual irregularities",
            "Some impact on quality of life",
            "Clinical evaluation recommended"
        ]
        recommendations = [
            "Schedule appointment with gynecologist for evaluation",
            "Keep detailed symptom diary",
            "Discuss symptoms with primary care provider",
            "Consider lifestyle modifications for symptom management",
            "Monitor for changes in symptom patterns"
        ]
    else:
        risk_level = "Low"
        findings = [
            "Minimal endometriosis symptoms present",
            "Mild or infrequent symptoms",
            "Limited impact on daily life",
            "Continue monitoring symptoms"
        ]
        recommendations = [
            "Continue monitoring symptoms",
            "Maintain regular gynecological check-ups",
            "Discuss any new or worsening symptoms with healthcare provider",
            "Practice healthy lifestyle habits",
            "Consider symptom tracking for early detection of changes"
        ]
    
    return {
        "risk_score": risk_percentage,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "findings": findings,
        "recommendations": recommendations
    }

@app.route("/risk")
def risk():
    """Risk assessment condition selection page"""
    return render_template("condition_selection.html", active_page="risk", user_name=session.get("user_name", "User"))

@app.route("/risk/pcos", methods=["GET", "POST"])
def risk_pcos():
    """PCOS risk assessment"""
    if request.method == "GET":
        # Clear any previous health_result to force fresh assessment
        if "health_result" in session:
            session.pop("health_result", None)
        
        # Initialize PCOS assessment only if it doesn't exist
        if "pcos_assessment" not in session:
            session["pcos_assessment"] = {"current_step": 0, "data": {}}
            session.modified = True
        
        # Always get current_step and assessment_data
        current_step = session["pcos_assessment"]["current_step"]
        assessment_data = session["pcos_assessment"]["data"]
        
        questionnaire_steps = get_pcos_questionnaire()
        total_steps = len(questionnaire_steps)
        
        # Safety check: if questionnaire is empty, reset to step 0
        if total_steps == 0:
            session["pcos_assessment"]["current_step"] = 0
            current_step = 0
            # Try to get questionnaire again
            questionnaire_steps = get_pcos_questionnaire()
            total_steps = len(questionnaire_steps)
        
        if current_step >= total_steps:
            # Calculate results
            results = calculate_pcos_risk(assessment_data)
            session["health_result"] = results
            session.modified = True
            return redirect(url_for("risk_results"))
        
        # Additional safety check to prevent IndexError
        if current_step < 0 or current_step >= len(questionnaire_steps):
            current_step = 0
            session["pcos_assessment"]["current_step"] = 0
        
        step_data = questionnaire_steps[current_step]
        
        return render_template(
            "risk.html",
            step_data=step_data,
            current_step=current_step,
            total_steps=total_steps,
            assessment_data=assessment_data,
            active_page="risk",
            user_name=session.get("user_name", "User")
        )
    
    elif request.method == "POST":
        current_step = session["pcos_assessment"]["current_step"]
        assessment_data = session["pcos_assessment"]["data"]
        
        questionnaire_steps = get_pcos_questionnaire()
        total_steps = len(questionnaire_steps)
        
        # Handle form submission
        if "next_step" in request.form:
            # Safety check before accessing questionnaire_steps
            if current_step < 0 or current_step >= len(questionnaire_steps):
                current_step = 0
                session["pcos_assessment"]["current_step"] = 0
            
            # Save current step answers
            step_data = questionnaire_steps[current_step]
            
            # Handle input fields
            if "input_fields" in step_data:
                for field in step_data["input_fields"]:
                    if field["id"] in request.form:
                        assessment_data[field["id"]] = request.form[field["id"]]
            
            # Handle questions
            if "questions" in step_data:
                for question in step_data["questions"]:
                    if question["id"] in request.form:
                        assessment_data[question["id"]] = request.form[question["id"]]
            
            session["pcos_assessment"]["data"] = assessment_data
            new_step = current_step + 1
            session["pcos_assessment"]["current_step"] = new_step
            session.modified = True
        
        elif "prev_step" in request.form:
            session["pcos_assessment"]["current_step"] = max(0, current_step - 1)
            session.modified = True
        
        return redirect(url_for("risk_pcos"))

@app.route("/risk/endometriosis", methods=["GET", "POST"])
def risk_endometriosis():
    """Endometriosis risk assessment"""
    if request.method == "GET":
        if "endometriosis_assessment" not in session:
            session["endometriosis_assessment"] = {"current_step": 0, "data": {}}
        
        current_step = session["endometriosis_assessment"]["current_step"]
        assessment_data = session["endometriosis_assessment"]["data"]
        
        questionnaire_steps = get_endometriosis_questionnaire()
        total_steps = len(questionnaire_steps)
        
        if current_step >= total_steps:
            # Calculate results
            results = calculate_endometriosis_risk(assessment_data)
            return render_template("endometriosis_results.html", results=results, active_page="risk", user_name=session.get("user_name", "User"))
        
        # Additional safety check to prevent IndexError
        if current_step < 0 or current_step >= len(questionnaire_steps):
            current_step = 0
            session["endometriosis_assessment"]["current_step"] = 0
        
        step_data = questionnaire_steps[current_step]
        
        return render_template(
            "endometriosis_risk.html",
            step_data=step_data,
            current_step=current_step,
            total_steps=total_steps,
            assessment_data=assessment_data,
            active_page="risk",
            user_name=session.get("user_name", "User")
        )
    
    elif request.method == "POST":
        current_step = session["endometriosis_assessment"]["current_step"]
        assessment_data = session["endometriosis_assessment"]["data"]
        
        questionnaire_steps = get_endometriosis_questionnaire()
        
        # Handle form submission
        if "next_step" in request.form:
            # Safety check before accessing questionnaire_steps
            if current_step < 0 or current_step >= len(questionnaire_steps):
                current_step = 0
                session["endometriosis_assessment"]["current_step"] = 0
            
            # Save current step answers
            step_data = questionnaire_steps[current_step]
            
            # Handle input fields
            if "input_fields" in step_data:
                for field in step_data["input_fields"]:
                    if field["id"] in request.form:
                        assessment_data[field["id"]] = request.form[field["id"]]
            
            # Handle questions
            if "questions" in step_data:
                for question in step_data["questions"]:
                    if question["id"] in request.form:
                        assessment_data[question["id"]] = request.form[question["id"]]
            
            session["endometriosis_assessment"]["data"] = assessment_data
            session["endometriosis_assessment"]["current_step"] = current_step + 1
            session.modified = True
        
        elif "prev_step" in request.form:
            session["endometriosis_assessment"]["current_step"] = max(0, current_step - 1)
            session.modified = True
        elif "start_new_assessment" in request.form:
            # Clear all assessment data and start fresh
            if "pcos_assessment" in session:
                session.pop("pcos_assessment", None)
            if "endometriosis_assessment" in session:
                session.pop("endometriosis_assessment", None)
            session.pop("health_result", None)
            session.modified = True
            return redirect(url_for("risk"))
        
        return redirect(url_for("risk_endometriosis"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
