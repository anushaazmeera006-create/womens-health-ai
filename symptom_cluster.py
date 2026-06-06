import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from datetime import datetime


class SymptomClusterer:
    def __init__(self, n_clusters=5):
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.cluster_labels = {
            0: {"name": "Normal Day", "emoji": "normal"},
            1: {"name": "Period Day", "emoji": "period"},
            2: {"name": "PMS Day", "emoji": "pms"},
            3: {"name": "Ovulation Day", "emoji": "ovulation"},
            4: {"name": "High Symptom Day", "emoji": "warning"}
        }

    def fit(self):
        """Fit the clustering model with sample data"""
        # Generate sample data for fitting
        sample_data = []
        for i in range(100):
            sample_data.append({
                "cramps": np.random.choice([0, 1, 2, 3]),
                "fatigue": np.random.choice([0, 1, 2, 3]),
                "nausea": np.random.choice([0, 1, 2, 3]),
                "mood_swings": np.random.choice([0, 1, 2, 3]),
                "acne": np.random.choice([0, 1, 2, 3]),
                "back_pain": np.random.choice([0, 1, 2, 3]),
                "flow_intensity": np.random.choice([1, 2, 3, 4]),
                "pain_level": np.random.choice([1, 2, 3, 4])
            })
        
        df = pd.DataFrame(sample_data)
        features = self._extract_features(df)
        self.kmeans.fit(features)

    def _extract_features(self, df):
        """Extract features for clustering"""
        features = df[["cramps", "fatigue", "nausea", "mood_swings", 
                      "acne", "back_pain", "flow_intensity", "pain_level"]].values
        return self.scaler.fit_transform(features)

    def predict_day(self, log_data):
        """Predict cluster for a single day's symptoms"""
        df = pd.DataFrame([log_data])
        features = self._extract_features(df)
        cluster_id = self.kmeans.predict(features)[0]
        return self.cluster_labels.get(cluster_id, {"name": "Unknown", "emoji": "question"})

    def get_pattern_summary(self, logs):
        """Get pattern summary from multiple logs"""
        if not logs:
            return {"message": "No data available"}
        
        cluster_counts = {}
        for log in logs:
            cluster = self.predict_day(log)
            cluster_name = cluster["name"]
            cluster_counts[cluster_name] = cluster_counts.get(cluster_name, 0) + 1
        
        # Find most common pattern
        most_common = max(cluster_counts.items(), key=lambda x: x[1]) if cluster_counts else ("Unknown", 0)
        
        return {
            "total_logs": len(logs),
            "cluster_distribution": cluster_counts,
            "most_common_pattern": most_common[0],
            "pattern_frequency": f"{most_common[1]}/{len(logs)} days"
        }
