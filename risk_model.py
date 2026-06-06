import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from feature_engineering import prepare_health_features


class HealthRiskModel:

    def __init__(self):
        self.base_dir = os.path.dirname(__file__)

        self.pcos_model = CalibratedClassifierCV(
            LogisticRegression(max_iter=2000), method="sigmoid"
        )
        self.endo_model = CalibratedClassifierCV(
            LogisticRegression(max_iter=2000), method="sigmoid"
        )

        self.pcos_scaler = StandardScaler()
        self.endo_scaler = StandardScaler()

        self.pcos_features = [
            "age", "bmi", "cycle_length", "cycle_irregular",
            "weight_gain", "hair_growth", "skin_darkening",
            "hair_loss", "pimples", "fast_food",
            "exercise", "sleep_hours",
            "cycle_variability", "hormonal_score", "lifestyle_risk",
        ]

        self.endo_features = [
            "age", "bmi", "cycle_length",
            "pelvic_pain", "heavy_bleeding",
            "pain_intercourse", "family_history_endo",
            "cycle_irregular", "exercise", "pain_score",
        ]

        self._train_models()

    def _clean_df(self, df):
        df.columns = df.columns.str.strip()
        df = df.replace({"Y": 1, "N": 0, "Yes": 1, "No": 0})
        return df.fillna(0)

    def _train_models(self):
        self._train_pcos()
        self._train_endo()

    # ================= PCOS =================
    def _train_pcos(self):
        path = os.path.join(self.base_dir, "PCOS_data_without_infertility.csv")
        df = self._clean_df(pd.read_csv(path))

        df["cycle_irregular"] = df["Cycle(R/I)"].apply(
            lambda x: 1 if str(x).strip() == "I" else 0
        )

        df["cycle_variability"] = abs(df["Cycle length(days)"] - 28)
        df["hormonal_score"] = (
            df["hair growth(Y/N)"] +
            df["Pimples(Y/N)"] +
            df["Hair loss(Y/N)"] +
            df["Skin darkening (Y/N)"]
        )
        df["lifestyle_risk"] = df["Fast food (Y/N)"]

        X = pd.DataFrame({
            "age": df["Age (yrs)"],
            "bmi": df["BMI"],
            "cycle_length": df["Cycle length(days)"],
            "cycle_irregular": df["cycle_irregular"],
            "weight_gain": df["Weight gain(Y/N)"],
            "hair_growth": df["hair growth(Y/N)"],
            "skin_darkening": df["Skin darkening (Y/N)"],
            "hair_loss": df["Hair loss(Y/N)"],
            "pimples": df["Pimples(Y/N)"],
            "fast_food": df["Fast food (Y/N)"],
            "exercise": df["Reg.Exercise(Y/N)"],
            "sleep_hours": 7,
            "cycle_variability": df["cycle_variability"],
            "hormonal_score": df["hormonal_score"],
            "lifestyle_risk": df["lifestyle_risk"],
        })

        # ✅ ensure all features exist
        for col in self.pcos_features:
            if col not in X:
                X[col] = 0

        X = X[self.pcos_features].apply(pd.to_numeric, errors="coerce").fillna(0)
        y = df["PCOS (Y/N)"].apply(pd.to_numeric, errors="coerce").fillna(0)

        self.pcos_model.fit(self.pcos_scaler.fit_transform(X), y)

    # ================= ENDO =================
    def _train_endo(self):
        path = os.path.join(self.base_dir, "endo.csv")
        df = self._clean_df(pd.read_csv(path))

        X = pd.DataFrame({
            "age": df["Age"],
            "bmi": df["BMI"],
            "cycle_length": 28,
            "cycle_irregular": df["Menstrual_Irregularity"],
            "pelvic_pain": (df["Chronic_Pain_Level"] > 5).astype(int),
            "heavy_bleeding": 0,
            "pain_intercourse": 0,
            "family_history_endo": 0,
            "exercise": 3,
        })

        X["pain_score"] = (
            X["pelvic_pain"] +
            X["pain_intercourse"] +
            X["heavy_bleeding"]
        )

        # ✅ fix: ensure all columns exist
        for col in self.endo_features:
            if col not in X:
                X[col] = 0

        X = X[self.endo_features].apply(pd.to_numeric, errors="coerce").fillna(0)
        y = df["Diagnosis"].apply(pd.to_numeric, errors="coerce").fillna(0)

        self.endo_model.fit(self.endo_scaler.fit_transform(X), y)

    # ================= PREDICT =================
    def predict_risk(self, user_input):
        X = prepare_health_features(user_input)

        pcos_prob = self.pcos_model.predict_proba(
            self.pcos_scaler.transform(X[self.pcos_features])
        )[0][1]

        endo_prob = self.endo_model.predict_proba(
            self.endo_scaler.transform(X[self.endo_features])
        )[0][1]

        f = X.iloc[0]
        pcos_prob += 0.01 * f["hormonal_score"]
        endo_prob += 0.015 * f["pain_score"]

        pcos_prob = float(np.clip(pcos_prob, 0.05, 0.95))
        endo_prob = float(np.clip(endo_prob, 0.05, 0.95))

        def format_output(p):
            pct = round(p * 100, 1)
            if pct < 35:
                return {"probability": pct, "risk_level": "Low"}
            elif pct < 65:
                return {"probability": pct, "risk_level": "Moderate"}
            else:
                return {"probability": pct, "risk_level": "High"}

        return {
            "PCOS": format_output(pcos_prob),
            "Endometriosis": format_output(endo_prob),
        }
