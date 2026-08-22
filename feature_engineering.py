import pandas as pd


def compute_bmi(weight, height):
    if height == 0:
        height = 160
    return round(weight / ((height / 100) ** 2), 1)


def prepare_health_features(user_input):

    if isinstance(user_input, dict):
        records = [user_input]
    else:
        records = user_input

    rows = []
    for rec in records:
        bmi = compute_bmi(
            rec.get("weight_kg", 60),
            rec.get("height_cm", 160),
        )

        rows.append({
            "age": rec.get("age", 25),
            "bmi": bmi,
            "cycle_length": rec.get("cycle_length", 28),
            "cycle_irregular": int(rec.get("cycle_irregular", False)),

            "weight_gain": int(rec.get("weight_gain", False)),
            "hair_growth": int(rec.get("hair_growth", False)),
            "pimples": int(rec.get("pimples", False)),
            "skin_darkening": int(rec.get("skin_darkening", False)),
            "hair_loss": int(rec.get("hair_loss", False)),

            "pelvic_pain": int(rec.get("pelvic_pain", False)),
            "heavy_bleeding": int(rec.get("heavy_bleeding", False)),
            "pain_intercourse": int(rec.get("pain_intercourse", False)),
            "family_history_endo": int(rec.get("family_history_endo", False)),

            "fast_food": int(rec.get("fast_food", False)),
            "exercise": rec.get("exercise", 3),
            "sleep_hours": rec.get("sleep_hours", 7),
        })

    df = pd.DataFrame(rows)

    df["cycle_variability"] = abs(df["cycle_length"] - 28)

    df["hormonal_score"] = (
        df["hair_growth"] +
        df["pimples"] +
        df["hair_loss"] +
        df["skin_darkening"]
    )

    df["pain_score"] = (
        df["pelvic_pain"] +
        df["pain_intercourse"] +
        df["heavy_bleeding"]
    )

    df["lifestyle_risk"] = (
        df["fast_food"] +
        (df["exercise"] < 2).astype(int) +
        (df["sleep_hours"] < 6).astype(int)
    )

    return df
