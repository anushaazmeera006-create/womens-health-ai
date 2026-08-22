import os
from datetime import datetime, timedelta

from flask import Flask, redirect, render_template, request, session, url_for

from cycle_predictor import CyclePredictor
from risk_model import HealthRiskModel
from symptom_cluster import SymptomClusterer


app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY", "period-tracker-dev-key")

predictor = CyclePredictor()
clusterer = SymptomClusterer()
clusterer.fit()
try:
    risk_model = HealthRiskModel()
except Exception:
    risk_model = None


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


def get_dashboard_data():
    dates = parsed_dates()
    prediction = predictor.predict_next(dates)
    next_period = prediction.get("next_predicted_date")
    if next_period is None:
        next_period = get_local_date()
    elif isinstance(next_period, datetime):
        next_period = next_period.date()

    days_until = (next_period - get_local_date()).days
    if days_until == 0:
        next_label = "Today"
    elif days_until > 0:
        next_label = f"in {days_until} days"
    else:
        next_label = f"{abs(days_until)} days ago"

    return {
        "avg_cycle": prediction.get("avg_cycle", 28),
        "predicted_length": prediction.get("predicted_length", 28),
        "next_period_label": next_label,
        "next_date": next_period.isoformat(),
        "period_dates": [d.isoformat() for d in dates],
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
        name = request.form.get("name", "").strip()
        if not name:
            return render_template("login.html", error="Please enter your name.")
        session["logged_in"] = True
        session["user_name"] = name
        return redirect(url_for("dashboard"))
    return render_template("login.html", error=None)


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
    ensure_state()
    data = get_dashboard_data()
    message = pop_message()
    return render_template(
        "dashboard.html",
        data=data,
        message=message,
        active_page="dashboard",
        user_name=session.get("user_name", "User"),
    )


@app.route("/cycle", methods=["GET", "POST"])
def cycle():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    ensure_state()
    if request.method == "POST":
        new_date = request.form.get("period_date", "").strip()
        period_length = request.form.get("period_length_days", "5").strip()
        try:
            parsed = datetime.fromisoformat(new_date).date().isoformat()
            session["period_length_days"] = max(1, min(15, int(period_length)))
        except ValueError:
            set_message("error", "Invalid date format.")
            return redirect(url_for("cycle"))

        date_list = set(session["period_dates"])
        date_list.add(parsed)
        session["period_dates"] = sorted(date_list)
        set_message("success", "Cycle details saved. Continue with daily check.")
        return redirect(url_for("symptoms", selected_date=parsed))

    data = get_dashboard_data()
    message = pop_message()
    return render_template(
        "cycle.html",
        data=data,
        message=message,
        active_page="cycle",
        user_name=session.get("user_name", "User"),
    )


@app.route("/symptoms", methods=["GET", "POST"])
def symptoms():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    ensure_state()
    selected_date = request.args.get("selected_date", get_local_date().isoformat())

    if request.method == "POST":
        selected_symptoms = request.form.getlist("symptoms")
        mood_state = request.form.get("mood_state", "")
        other_symptom = request.form.get("other_symptom", "").strip()
        cycle_phase = request.form.get("cycle_phase", "Follicular")
        had_period = request.form.get("had_period", "No")

        log = {
            "selected_date": request.form.get("selected_date", selected_date),
            "had_period": had_period,
            "cycle_phase": cycle_phase,
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

        logs = session["symptom_logs"]
        logs.append(log)
        session["symptom_logs"] = logs

        try:
            cluster = clusterer.predict_day(log)
            set_message("success", f"{cluster['emoji']}
    ]},
    {cluster['name']}
    ] day logged.")
        except Exception as exc:
            set_message("error", f"Clustering failed: {exc}")
        return redirect(url_for("symptoms"))

    data = get_dashboard_data()
    message = pop_message()
    return render_template(
        "symptoms.html",
        data=data,
        message=message,
        active_page="symptoms",
        selected_date=selected_date,
        user_name=session.get("user_name", "User"),
    )


@app.route("/risk", methods=["GET", "POST"])
def risk():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    ensure_state()
    
    # Initialize assessment session if not exists
    if "pcos_assessment" not in session:
        session["pcos_assessment"] = {
            "current_step": 0,
            "data": {
                # Step 1: Age & Basic Info
                "age_group": "", "weight": "", "height": "",
                # Step 2: Cycle Irregularity
                "cycle_regularity": "", "cycle_length_variation": "", "menstrual_flow": "",
                # Step 3: Hormonal Symptoms
                "excess_hair_growth": "", "hair_thinning": "", "severe_acne": "",
                # Step 4: Weight & Metabolism
                "rapid_weight_gain": "", "difficulty_losing_weight": "",
                # Step 5: Insulin Resistance Indicators
                "skin_darkening": "", "sugar_cravings": "", "fatigue_after_meals": "",
                # Step 6: Lifestyle Factors
                "fast_food_frequency": "", "exercise_level": "", "sleep_quality": "",
                # Step 7: Mental Health
                "mood_swings": "", "anxiety": "", "depression": "",
                # Step 8: Family History
                "family_pcos_mother": "", "family_pcos_sister": ""
            }
        }
        session.modified = True  # Ensure session is saved
    
    # Define questionnaire steps
    questionnaire_steps = [
        {
            "id": "age_basic",
            "title": "About You",
            "subtitle": "Let's get to know you better",
            "questions": [
                {
                    "id": "age_group",
                    "question": "How old are you?",
                    "options": [
                        {"value": "0", "label": "Under 18 years", "explanation": "PCOS is usually found in younger women"},
                        {"value": "1", "label": "18-25 years", "explanation": "This is the most common age group for PCOS"},
                        {"value": "2", "label": "26-35 years", "explanation": "PCOS is most common in this age range"},
                        {"value": "3", "label": "36-45 years", "explanation": "Still important to check in this age group"},
                        {"value": "4", "label": "Over 45 years", "explanation": "Less common but still possible"}
                    ]}
    ],
                {
                    "id": "weight",
                    "question": "What's your current weight?",
                    "options": [
                        {"value": "45", "label": "45 kg (99 lbs)", "explanation": "Light weight range"},
                        {"value": "55", "label": "55 kg (121 lbs)", "explanation": "Average healthy weight"},
                        {"value": "65", "label": "65 kg (143 lbs)", "explanation": "Above average weight"},
                        {"value": "75", "label": "75 kg (165 lbs)", "explanation": "Higher weight range"},
                        {"value": "85", "label": "85 kg (187 lbs)", "explanation": "High weight range"},
                        {"value": "95", "label": "95+ kg (209+ lbs)", "explanation": "Very high weight range"}
                    ]}
    ],
                {
                    "id": "height",
                    "question": "How tall are you?",
                    "options": [
                        {"value": "150", "label": "150 cm (4'11\")", "explanation": "Shorter height"},
                        {"value": "160", "label": "160 cm (5'3\")", "explanation": "Average height for women"},
                        {"value": "165", "label": "165 cm (5'5\")", "explanation": "Taller than average"},
                        {"value": "170", "label": "170 cm (5'7\")", "explanation": "Tall height"},
                        {"value": "175", "label": "175 cm (5'9\")", "explanation": "Very tall height"},
                        {"value": "180", "label": "180+ cm (5'11+)", "explanation": "Extremely tall height"}
                    ]}
    ]
            ]}
    ],
        {
            "id": "cycle_irregularity",
            "title": "Your Monthly Cycle",
            "subtitle": "Let's understand your period patterns",
            "questions": [
                {
                    "id": "cycle_regularity",
                    "question": "How regular are your periods?",
                    "options": [
                        {"value": "0", "label": "Very regular (every 26-32 days)", "explanation": "This is a healthy pattern"},
                        {"value": "1", "label": "Sometimes irregular", "explanation": "Slight changes in timing"},
                        {"value": "2", "label": "Often irregular", "explanation": "Frequent changes in timing"},
                        {"value": "3", "label": "Very irregular or missing periods", "explanation": "This needs medical attention"}
                    ]}
    ],
                {
                    "id": "cycle_length_variation",
                    "question": "How much do your period dates change?",
                    "options": [
                        {"value": "0", "label": "Less than 3 days difference", "explanation": "This is normal"},
                        {"value": "1", "label": "3-7 days difference", "explanation": "Small changes"},
                        {"value": "2", "label": "1-2 weeks difference", "explanation": "Moderate changes"},
                        {"value": "3", "label": "More than 2 weeks difference", "explanation": "Large changes in cycle"}
                    ]}
    ],
                {
                    "id": "menstrual_flow",
                    "question": "How heavy are your periods usually?",
                    "options": [
                        {"value": "0", "label": "Normal flow (4-7 days)", "explanation": "This is a healthy pattern"},
                        {"value": "1", "label": "Very heavy bleeding", "explanation": "May be a sign of hormone issues"},
                        {"value": "2", "label": "Very light bleeding", "explanation": "May mean ovulation problems"},
                        {"value": "3", "label": "No periods at all", "explanation": "This needs medical attention"}
                    ]}
    ]
            ]}
    ],
        {
            "id": "hormonal_symptoms",
            "title": "Your Body Changes",
            "subtitle": "Let's check for common PCOS signs",
            "questions": [
                {
                    "id": "excess_hair_growth",
                    "question": "Do you have more hair on your face or body than usual?",
                    "options": [
                        {"value": "0", "label": "No extra hair", "explanation": "This is normal for you"},
                        {"value": "1", "label": "A little extra hair", "explanation": "Slight increase in hair growth"},
                        {"value": "2", "label": "Quite a bit extra hair", "explanation": "Noticeable increase in hair growth"},
                        {"value": "3", "label": "A lot of extra hair", "explanation": "Significant increase in hair growth"}
                    ]}
    ],
                {
                    "id": "hair_thinning",
                    "question": "Are you losing more hair than usual, especially on top of your head?",
                    "options": [
                        {"value": "0", "label": "No hair loss", "explanation": "Your hair is normal and healthy"},
                        {"value": "1", "label": "A little thinning", "explanation": "Early signs of hair changes"},
                        {"value": "2", "label": "Noticeable thinning", "explanation": "Your hair is getting thinner over time"},
                        {"value": "3", "label": "A lot of thinning", "explanation": "Significant hair loss pattern"}
                    ]}
    ],
                {
                    "id": "severe_acne",
                    "question": "How bad is your acne or skin breakouts?",
                    "options": [
                        {"value": "0", "label": "Clear or almost clear skin", "explanation": "Your skin is doing great"},
                        {"value": "1", "label": "Some pimples sometimes", "explanation": "Normal teenage/adult skin"},
                        {"value": "2", "label": "Frequent breakouts", "explanation": "Hormone-related skin issues"},
                        {"value": "3", "label": "Severe acne all the time", "explanation": "Significant hormone imbalance signs"}
                    ]}
    ]
            ]}
    ],
        {
            "id": "weight_metabolism",
            "title": "Your Weight Changes",
            "subtitle": "Let's understand your body's metabolism",
            "questions": [
                {
                    "id": "rapid_weight_gain",
                    "question": "Have you gained weight quickly recently?",
                    "options": [
                        {"value": "0", "label": "No, my weight is stable", "explanation": "This is a healthy pattern"},
                        {"value": "1", "label": "Yes, a little bit (5-10 lbs)", "explanation": "Small changes in weight"},
                        {"value": "2", "label": "Yes, quite a bit (10-20 lbs)", "explanation": "Your metabolism may be slowing"},
                        {"value": "3", "label": "Yes, a lot (20+ lbs)", "explanation": "Your body is storing more fat"}
                    ]}
    ],
                {
                    "id": "difficulty_losing_weight",
                    "question": "Is it hard for you to lose weight even when you try?",
                    "options": [
                        {"value": "0", "label": "No, I can lose weight normally", "explanation": "Your metabolism is working well"},
                        {"value": "1", "label": "A little harder than expected", "explanation": "Might be some resistance"},
                        {"value": "2", "label": "Much harder than it should be", "explanation": "Your body fights weight loss"},
                        {"value": "3", "label": "Almost impossible to lose weight", "explanation": "Your metabolism needs medical attention"}
                    ]}
    ]
            ]}
    ],
        {
            "id": "insulin_resistance",
            "title": "Your Blood Sugar Signs",
            "subtitle": "Let's check how your body handles sugar",
            "questions": [
                {
                    "id": "skin_darkening",
                    "question": "Do you have dark, thick skin patches on your neck, armpits or other areas?",
                    "options": [
                        {"value": "0", "label": "No dark patches", "explanation": "Your skin looks normal and healthy"},
                        {"value": "1", "label": "A few light patches", "explanation": "Early signs your body is struggling with sugar"},
                        {"value": "2", "label": "Noticeable dark patches", "explanation": "Your body has sugar processing issues"},
                        {"value": "3", "label": "Very dark, thick patches", "explanation": "Your body needs medical attention for sugar issues"}
                    ]}
    ],
                {
                    "id": "sugar_cravings",
                    "question": "How often do you really want to eat sweet foods?",
                    "options": [
                        {"value": "0", "label": "Rarely or never", "explanation": "Your blood sugar is stable"},
                        {"value": "1", "label": "Sometimes", "explanation": "Mild blood sugar ups and downs"},
                        {"value": "2", "label": "Often", "explanation": "Your blood sugar goes up and down a lot"},
                        {"value": "3", "label": "All the time, can't stop thinking about sweets", "explanation": "Your body has trouble with blood sugar control"}
                    ]}
    ],
                {
                    "id": "fatigue_after_meals",
                    "question": "Do you feel very tired or sleepy after you eat?",
                    "options": [
                        {"value": "0", "label": "No, I feel normal after eating", "explanation": "Your body handles food well"},
                        {"value": "1", "label": "Sometimes I get sleepy", "explanation": "Mild blood sugar spikes after meals"},
                        {"value": "2", "label": "Often I feel very tired", "explanation": "Your blood sugar goes up and down after eating"},
                        {"value": "3", "label": "Always feel like I need to nap after eating", "explanation": "Your body struggles with blood sugar after meals"}
                    ]}
    ]
            ]}
    ],
            {
            "id": "lifestyle_factors",
            "title": "Your Daily Habits",
            "subtitle": "Let's understand your lifestyle patterns",
            "questions": [
                {
                    "id": "fast_food_frequency",
                    "question": "How often do you eat fast food or processed meals?",
                    "options": [
                        {"value": "0", "label": "Rarely or never", "explanation": "You eat mostly fresh, home-cooked food"},
                        {"value": "1", "label": "Sometimes (1-2 times a week)", "explanation": "You mix healthy and convenience foods"},
                        {"value": "2", "label": "Often (3-5 times a week)", "explanation": "You rely on convenience foods frequently"},
                        {"value": "3", "label": "Almost every day", "explanation": "You eat mostly processed foods"}
                    ]}
    ],
                {
                    "id": "exercise_level",
                    "question": "How much do you move your body or exercise?",
                    "options": [
                        {"value": "0", "label": "Very active (3+ times a week)", "explanation": "Great for your hormones and health"},
                        {"value": "1", "label": "Sometimes active (1-2 times a week)", "explanation": "Good but could be more consistent"},
                        {"value": "2", "label": "A little active (rarely)", "explanation": "Your body needs more movement"},
                        {"value": "3", "label": "Not very active (mostly sitting)", "explanation": "Your body needs much more movement"}
                    ]}
    ],
                {
                    "id": "sleep_quality",
                    "question": "How well do you usually sleep at night?",
                    "options": [
                        {"value": "0", "label": "Great sleep (7-8 hours, wake up refreshed)", "explanation": "Your body gets the rest it needs"},
                        {"value": "1", "label": "Okay sleep (6-7 hours, sometimes wake up)", "explanation": "Your sleep could be better"},
                        {"value": "2", "label": "Poor sleep (5-6 hours, wake up tired)", "explanation": "Your body needs more quality sleep"},
                        {"value": "3", "label": "Very poor sleep (less than 5 hours)", "explanation": "Your body is not getting enough rest"}
                    ]}
    ]
            ]}
    ],
        {
            "id": "family_history",
            "title": "Your Family Health",
            "subtitle": "Let's understand your family background",
            "questions": [
                {
                    "id": "family_pcos_mother",
                    "question": "Does your mother have PCOS?",
                    "options": [
                        {"value": "0", "label": "No", "explanation": "No family risk from your mother"},
                        {"value": "1", "label": "Yes", "explanation": "PCOS can run in families"},
                        {"value": "2", "label": "I don't know", "explanation": "Family history is unclear"}
                    ]}
    ],
                },
                {
                    "question": "Do any of your sisters have PCOS?",
                    "options": [
                        {"value": "0", "label": "No", "explanation": "No family risk from your sisters"},
                        {"value": "1", "label": "Yes", "explanation": "PCOS can run in families"},
                        {"value": "2", "label": "I don't know", "explanation": "Family history is unclear"}
                    ]}
    ]
            ]}
    ]
    ]
    
    if request.method == "POST":
        current_step = session["pcos_assessment"]["current_step"]
        assessment_data = session["pcos_assessment"]["data"]
        
        # Debug: Print form data
        print(f"DEBUG: Form data received: {dict(request.form)}")
        print(f"DEBUG: Current step: {current_step}")
        print(f"DEBUG: Assessment data before: {assessment_data}")
        
        # Handle form submission for current step
        if "next_step" in request.form:
            # Save current step answers
            step_data = questionnaire_steps[current_step]
            for question in step_data["questions"]:
                if question["id"] in request.form:
                    assessment_data[question["id"]] = request.form[question["id"]]
                    print(f"DEBUG: Saved {question['id']}
    ] = {request.form[question['id']]}
    ]")
            
            # Update session with saved data
            session["pcos_assessment"]["data"] = assessment_data
            print(f"DEBUG: Assessment data after: {assessment_data}")
            
            # Move to next step or calculate results
            if current_step < len(questionnaire_steps) - 1:
                session["pcos_assessment"]["current_step"] = current_step + 1
                session.modified = True  # Ensure session is saved
                print(f"DEBUG: Moving to step {current_step + 1}")
            else:
                # Calculate final risk assessment
                risk_result = calculate_comprehensive_pcos_risk(assessment_data)
                session["health_result"] = risk_result
                set_message("success", "PCOS risk assessment complete!")
                return redirect(url_for("risk_results"))
        
        elif "prev_step" in request.form:
            # Go to previous step
            if current_step > 0:
                session["pcos_assessment"]["current_step"] = current_step - 1
                session.modified = True  # Ensure session is saved
        
        elif "reset_assessment" in request.form:
            # Reset assessment
            session.pop("pcos_assessment", None)
            session.pop("health_result", None)
            set_message("success", "Assessment reset successfully.")
            return redirect(url_for("risk"))
    
    data = get_dashboard_data()
    health_result = session.pop("health_result", None)
    message = pop_message()
    
    # Get current step data
    current_step = session["pcos_assessment"]["current_step"]
    current_step_data = questionnaire_steps[current_step]
    assessment_data = session["pcos_assessment"]["data"]
    
    return render_template(
        "risk.html",
        data=data,
        health_result=health_result,
        message=message,
        active_page="risk",
        user_name=session.get("user_name", "User"),
        current_step=current_step,
        total_steps=len(questionnaire_steps),
        step_data=current_step_data,
        assessment_data=assessment_data,
    )


@app.route("/risk_results")
def risk_results():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    
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


def calculate_comprehensive_pcos_risk(assessment_data):
    """Calculate PCOS risk based on comprehensive medical assessment"""
    
    # Risk factor weights based on medical importance
    risk_weights = {
        "age_group": 0.05,
        "weight": 0.06,
        "height": 0.04,
        "cycle_regularity": 0.15,
        "cycle_length_variation": 0.10,
        "menstrual_flow": 0.10,
        "excess_hair_growth": 0.12,
        "hair_thinning": 0.08,
        "severe_acne": 0.08,
        "rapid_weight_gain": 0.08,
        "difficulty_losing_weight": 0.08,
        "skin_darkening": 0.06,
        "sugar_cravings": 0.04,
        "fatigue_after_meals": 0.04,
        "fast_food_frequency": 0.03,
        "exercise_level": 0.03,
        "sleep_quality": 0.03,
        "mood_swings": 0.03,
        "anxiety": 0.02,
        "depression": 0.02,
        "family_pcos_mother": 0.10,
        "family_pcos_sister": 0.08,
    }
    
    total_risk = 0
    risk_factors = {}
    recommendations = []
    
    for factor, weight in risk_weights.items():
        value = float(assessment_data.get(factor, 0))
        
        # Normalize values (assuming 0-3 scale for most factors)
        if factor == "weight":
            # Weight special handling (convert to BMI calculation)
            weight_val = float(assessment_data.get("weight", 55))
            height_val = float(assessment_data.get("height", 160))
            if height_val > 0:
                height_m = height_val / 100  # Convert cm to meters
                bmi = weight_val / (height_m * height_m)
                if bmi < 18.5:
                    normalized = 0.1
                elif bmi < 25:
                    normalized = 0.2
                elif bmi < 30:
                    normalized = 0.6
                else:
                    normalized = 0.9
            else:
                normalized = 0.5  # Default if no height
        elif factor == "height":
            # Height special handling (lower weight for height alone)
            normalized = 0.2  # Height is less directly predictive than weight/BMI
        else:
            if factor == "age_group":
                # Age special handling
                if value <= 1:
                    normalized = 0.3
                elif value <= 2:
                    normalized = 0.7
                elif value <= 3:
                    normalized = 0.6
                else:
                    normalized = 0.4
            else:
                # Standard 0-3 scale normalization
                normalized = value / 3.0
        
        risk_factors[factor] = normalized
        total_risk += normalized * weight
    
    # Generate recommendations based on high-risk factors
    if risk_factors.get("cycle_regularity", 0) > 0.6:
        recommendations.append("Consult with a healthcare provider about menstrual irregularities")
    if risk_factors.get("excess_hair_growth", 0) > 0.5:
        recommendations.append("Discuss excessive hair growth with a healthcare provider")
    # Calculate BMI from weight and height for recommendations
    weight_val = float(assessment_data.get("weight", 55))
    height_val = float(assessment_data.get("height", 160))
    calculated_bmi = 0
    if height_val > 0:
        height_m = height_val / 100
        calculated_bmi = weight_val / (height_m * height_m)
    
    if calculated_bmi > 25:
        recommendations.append("Consider weight management through balanced diet and regular exercise")
    if risk_factors.get("skin_darkening", 0) > 0.5:
        recommendations.append("Skin darkening may indicate insulin resistance - consider medical evaluation")
    if risk_factors.get("family_pcos_mother", 0) > 0 or risk_factors.get("family_pcos_sister", 0) > 0:
        recommendations.append("Family history increases risk - regular check-ups recommended")
    if risk_factors.get("difficulty_losing_weight", 0) > 0.6:
        recommendations.append("Difficulty losing weight may indicate insulin resistance")
    if risk_factors.get("sugar_cravings", 0) > 0.6:
        recommendations.append("Frequent sugar cravings suggest blood sugar instability")
    if risk_factors.get("exercise_level", 0) > 0.6:
        recommendations.append("Regular exercise can help manage PCOS symptoms")
    if risk_factors.get("sleep_quality", 0) > 0.6:
        recommendations.append("Poor sleep affects hormonal balance - aim for 7-9 hours")
    
    if not recommendations:
        recommendations.append("Your current profile shows lower PCOS risk factors")
    
    # Determine risk level
    risk_percentage = min(95, int(total_risk * 100))
    if risk_percentage < 35:
        risk_level = "Low"
    elif risk_percentage < 70:
        risk_level = "Medium"
    else:
        risk_level = "High"
    
    return {
        "risk_percentage": risk_percentage,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "recommendations": recommendations,
        "assessment_summary": generate_assessment_summary(risk_factors)
    }


def generate_assessment_summary(risk_factors):
    """Generate a summary of key findings"""
    summary = []
    
    if risk_factors.get("cycle_regularity", 0) > 0.6:
        summary.append("Significant menstrual irregularity detected")
    if risk_factors.get("excess_hair_growth", 0) > 0.5:
        summary.append("High androgen symptoms present")
    if risk_factors.get("bmi", 0) > 0.6:
        summary.append("Weight-related metabolic factors")
    if risk_factors.get("skin_darkening", 0) > 0.5:
        summary.append("Insulin resistance indicators")
    if risk_factors.get("family_pcos_mother", 0) > 0 or risk_factors.get("family_pcos_sister", 0) > 0:
        summary.append("Genetic predisposition present")
    
    if not summary:
        summary.append("Few significant PCOS risk factors identified")
    
    return summary


@app.get("/patterns")
def patterns():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    ensure_state()
    logs = session.get("symptom_logs", [])
    summary = None

    if len(logs) < 3:
        set_message("error", "Need at least 3 logs for pattern analysis.")
    else:
        try:
            summary = clusterer.get_pattern_summary(logs)
            if summary:
                dom = summary["dominant"]
                set_message("success", f"Pattern found: {dom['emoji']}
    ]},
    {dom['name']}
    ]")
            else:
                set_message("error", "No pattern summary available.")
        except Exception as exc:
            set_message("error", f"Pattern analysis failed: {exc}")

    data = get_dashboard_data()
    message = pop_message()
    return render_template(
        "patterns.html",
        data=data,
        summary=summary,
        message=message,
        active_page="patterns",
        user_name=session.get("user_name", "User"),
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
