import os
import pickle
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_FILE = BASE_DIR / 'ml' / 'model' / 'model.pkl'
DATA_FILE = BASE_DIR / 'data' / 'customer_churn.csv'

class PredictionService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PredictionService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.model = None
        self.encoders = {}
        self.feature_columns = []
        self._load_system()
        self._initialized = True

    def _load_system(self):
        logger.info("Initializing SmartChurn Prediction Service...")

        # Load reference dataset to fit encoders exactly as trained
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
            df['TotalCharges'] = df['TotalCharges'].fillna(df['TotalCharges'].mean())

            X_raw = df.drop(columns=['Churn'], errors='ignore')
            self.feature_columns = [col for col in X_raw.columns if col != 'customerID']

            for col in self.feature_columns:
                if not pd.api.types.is_numeric_dtype(X_raw[col]):
                    le = LabelEncoder()
                    X_raw[col] = le.fit_transform(X_raw[col].astype(str))
                    self.encoders[col] = le
        else:
            logger.warning(f"Data file {DATA_FILE} not found. Fallback mode.")
            self.feature_columns = [
                'gender', 'SeniorCitizen', 'Partner', 'Dependents', 'tenure',
                'PhoneService', 'MultipleLines', 'InternetService', 'OnlineSecurity',
                'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV',
                'StreamingMovies', 'Contract', 'PaperlessBilling', 'PaymentMethod',
                'MonthlyCharges', 'TotalCharges'
            ]

        # Load Model
        if os.path.exists(MODEL_FILE):
            with open(MODEL_FILE, 'rb') as f:
                self.model = pickle.load(f)
            logger.info("Random Forest Model loaded successfully.")
        else:
            logger.error(f"Model file {MODEL_FILE} not found!")

    def predict_single(self, input_dict):
        """
        Takes raw dictionary of input telemetry and returns detailed prediction dict.
        """
        if self.model is None:
            self._load_system()
            if self.model is None:
                raise RuntimeError("ML Model is unavailable.")

        # Clean/Format inputs into DataFrame row
        row = {}
        for col in self.feature_columns:
            val = input_dict.get(col, input_dict.get(col.lower(), ""))
            row[col] = val

        df_input = pd.DataFrame([row])

        # Preprocessing & Encoding
        for col in self.feature_columns:
            if col in self.encoders:
                known_classes = list(self.encoders[col].classes_)
                val_str = str(df_input.loc[0, col])
                if val_str not in known_classes:
                    val_str = known_classes[0]
                df_input[col] = self.encoders[col].transform([val_str])[0]
            else:
                try:
                    df_input[col] = float(df_input.loc[0, col])
                except (ValueError, TypeError):
                    df_input[col] = 0.0

        # Model Inference
        df_encoded = df_input[self.feature_columns]
        prediction_int = int(self.model.predict(df_encoded)[0])
        probabilities = self.model.predict_proba(df_encoded)[0]

        churn_prob = float(probabilities[1]) if len(probabilities) > 1 else float(prediction_int)
        confidence = float(max(probabilities)) if len(probabilities) > 1 else 1.0

        is_churn = (prediction_int == 1) or (churn_prob >= 0.5)

        # Determine Risk Level
        if churn_prob <= 0.30:
            risk_level = 'Low'
        elif churn_prob <= 0.60:
            risk_level = 'Medium'
        else:
            risk_level = 'High'

        # Analyze key risk drivers
        key_factors = self._analyze_risk_factors(input_dict, churn_prob)

        return {
            'is_churn': is_churn,
            'prediction_label': 'Churn' if is_churn else 'Safe',
            'churn_probability': churn_prob,
            'churn_percentage': round(churn_prob * 100, 1),
            'risk_level': risk_level,
            'confidence': round(confidence * 100, 1),
            'key_factors': key_factors,
            'raw_input': input_dict
        }

    def _analyze_risk_factors(self, data, churn_prob):
        factors = []
        contract = str(data.get('Contract', data.get('contract', ''))).lower()
        tenure = float(data.get('tenure', 0) or 0)
        monthly = float(data.get('MonthlyCharges', data.get('monthly_charges', 0)) or 0)
        internet = str(data.get('InternetService', data.get('internet_service', ''))).lower()
        tech_sup = str(data.get('TechSupport', data.get('tech_support', ''))).lower()
        security = str(data.get('OnlineSecurity', data.get('online_security', ''))).lower()

        if 'month' in contract:
            factors.append("Month-to-Month Contract (Highest churn correlation)")
        if tenure < 12:
            factors.append(f"Short Customer Tenure ({int(tenure)} months)")
        if monthly > 70:
            factors.append(f"High Monthly Charges (${monthly:.2f})")
        if 'fiber' in internet:
            factors.append("Fiber Optic Internet Service (Elevated churn rate in demographic)")
        if 'no' in tech_sup:
            factors.append("No Tech Support Subscription")
        if 'no' in security:
            factors.append("No Online Security Subscription")

        if not factors and churn_prob < 0.3:
            factors.append("Strong tenure and loyal contract profile")

        return factors

# Global singleton helper
def get_prediction_service():
    return PredictionService()
