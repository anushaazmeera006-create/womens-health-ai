import pandas as pd
import os
from datetime import datetime, timedelta, date


class CyclePredictor:

    DATE_COL = "Cycle Start Date"
    LENGTH_COL = "Cycle Length"
    USER_COL = "User ID"

    def __init__(self, csv_path=None):
        try:
            base_dir = os.path.dirname(__file__)
            path = csv_path or os.path.join(base_dir, "cycle.csv")

            self.df = pd.read_csv(path)
            self.df.columns = self.df.columns.str.strip()

            if self.DATE_COL in self.df:
                self.df[self.DATE_COL] = pd.to_datetime(
                    self.df[self.DATE_COL], errors="coerce"
                )
        except Exception:
            self.df = pd.DataFrame()

    @staticmethod
    def _to_datetime(d):
        if isinstance(d, datetime):
            return d
        if isinstance(d, date):
            return datetime(d.year, d.month, d.day)
        return pd.Timestamp(d).to_pydatetime()

    def _get_cycle_lengths(self, dates):
        if len(dates) < 2:
            return []

        dts = sorted([self._to_datetime(d) for d in dates])
        return [(dts[i] - dts[i - 1]).days for i in range(1, len(dts))]

    def predict_next(self, dates):

        if not dates or len(dates) < 2:
            return {
                "predicted_length": 28,
                "avg_cycle": 28,
                "std_dev": 0,
            }

        lengths = self._get_cycle_lengths(dates)

        if not lengths:
            return {
                "predicted_length": 28,
                "avg_cycle": 28,
                "std_dev": 0,
            }

        avg = int(round(sum(lengths) / len(lengths)))
        std_dev = round(
            (sum((l - avg) ** 2 for l in lengths) / len(lengths)) ** 0.5, 1
        ) if len(lengths) > 1 else 0

        last = self._to_datetime(max(dates))

        return {
            "predicted_length": avg,
            "next_predicted_date": last + timedelta(days=avg),
            "avg_cycle": avg,
            "std_dev": std_dev,
        }

    def predict_for_user(self, user_id):

        if self.df.empty:
            return {"error": "Dataset not loaded"}

        user_df = self.df[self.df[self.USER_COL] == user_id]

        if user_df.empty:
            return {"error": f"No data for user {user_id}"}

        dates = user_df[self.DATE_COL].dropna().tolist()
        return self.predict_next(dates)
