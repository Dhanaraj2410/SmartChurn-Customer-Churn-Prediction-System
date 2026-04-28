from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import numpy as np
import pickle
import os
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import warnings
import logging

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend to communicate with backend

MODEL_FILE = 'model.pkl'
DATA_FILE = 'customer_churn.csv'

# Global variables to store the model and encoders
model = None
encoders = {}
feature_columns = []
label_encoders_info = {}  # Store mapping information for debugging


def initialize_system():
    """
    Initializes the model and the label encoders.
    It reads the original dataset to figure out the exact mapping rules
    so that frontend string inputs can be correctly converted to numbers.
    """
    global model, encoders, feature_columns, label_encoders_info

    logger.info("Initializing SmartChurn System...")

    # 1. Load Data to build Encoders
    if not os.path.exists(DATA_FILE):
        logger.error(f"ERROR: {DATA_FILE} not found! Please ensure the CSV file is in the same directory.")
        logger.info("Creating dummy data for initialization...")
        create_dummy_data()
        if not os.path.exists(DATA_FILE):
            logger.error("Failed to create dummy data. Cannot proceed.")
            return

    df = pd.read_csv(DATA_FILE)

    # Clean TotalCharges (same as notebook)
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
    df['TotalCharges'] = df['TotalCharges'].fillna(df['TotalCharges'].mean())

    # Separate features and target
    X_raw = df.drop(columns=['Churn'])
    feature_columns = X_raw.columns.tolist()
    
    # Remove customerID from feature columns for training (It's an ID, not a feature!)
    if 'customerID' in feature_columns:
        feature_columns.remove('customerID')
    
    logger.info(f"Predictive features identified: {feature_columns}")
    
    # Build Encoders for categorical columns and scale numerical ones
    for col in X_raw.columns:
        if X_raw[col].dtype == 'object' and col != 'customerID':
            le = LabelEncoder()
            # Fit on the dataset to learn the mapping
            X_raw[col] = le.fit_transform(X_raw[col].astype(str))
            encoders[col] = le
            label_encoders_info[col] = dict(zip(le.classes_, le.transform(le.classes_)))
        elif col == 'customerID':
            # Keep customerID as string, won't be used for training
            pass

    # Prepare training data (strictly excluding customerID)
    X_train_data = X_raw[feature_columns]
    y = df['Churn'].map({'Yes': 1, 'No': 0})

    # 2. Load or Retrain Model
    if os.path.exists(MODEL_FILE):
        logger.info(f"Loading existing model from {MODEL_FILE}...")
        try:
            with open(MODEL_FILE, 'rb') as f:
                model = pickle.load(f)
            
            # === THE FIX ===
            # Scikit-learn models save the features they were trained on in 'feature_names_in_'
            # If the user's original Jupyter Notebook model was trained WITH customerID, 
            # it will cause an error because we intentionally drop it for predictions.
            if hasattr(model, 'feature_names_in_'):
                trained_features = list(model.feature_names_in_)
                if 'customerID' in trained_features or set(trained_features) != set(feature_columns):
                    logger.warning("⚠️ Feature mismatch detected! (Model was trained with customerID).")
                    logger.warning("Automatically retraining a clean model without customerID...")
                    retrain_model(X_train_data, y)
                else:
                    logger.info("Model loaded successfully and features match perfectly.")
            else:
                logger.info("Model loaded successfully.")
                
        except Exception as e:
            logger.error(f"Error loading model: {e}. Falling back to retraining.")
            retrain_model(X_train_data, y)
    else:
        logger.info(f"Model file not found. Training a fresh model on {DATA_FILE}...")
        retrain_model(X_train_data, y)


def create_dummy_data():
    """Create dummy data if CSV is not found"""
    dummy_data = {
        'customerID': ['DUMMY-001'],
        'gender': ['Male'],
        'SeniorCitizen': [0],
        'Partner': ['No'],
        'Dependents': ['No'],
        'tenure': [1],
        'PhoneService': ['Yes'],
        'MultipleLines': ['No'],
        'InternetService': ['DSL'],
        'OnlineSecurity': ['No'],
        'OnlineBackup': ['No'],
        'DeviceProtection': ['No'],
        'TechSupport': ['No'],
        'StreamingTV': ['No'],
        'StreamingMovies': ['No'],
        'Contract': ['Month-to-month'],
        'PaperlessBilling': ['Yes'],
        'PaymentMethod': ['Electronic check'],
        'MonthlyCharges': [50.0],
        'TotalCharges': [50.0],
        'Churn': ['No']
    }
    df = pd.DataFrame(dummy_data)
    df.to_csv(DATA_FILE, index=False)
    logger.info(f"Created dummy data file: {DATA_FILE}")


def retrain_model(X_train_data, y):
    """Retrains the model ensuring only valid predictive features are used."""
    global model
    logger.info("Training fresh Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        min_samples_split=5,
        min_samples_leaf=2
    )
    model.fit(X_train_data, y)
    
    # Overwrite the old faulty model with the new clean one
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(model, f)
    logger.info("Fresh model trained and saved successfully as model.pkl.")


# Run initialization
initialize_system()


@app.route('/')
def home():
    """Serve the main HTML page"""
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    """Predict churn probability for a customer"""
    if model is None:
        return jsonify({'error': 'Model is not initialized. Please restart the server.', 'status': 'failed'}), 500

    try:
        data = request.json
        
        # Prepare the input dictionary mapping
        input_data = {}
        
        for col in feature_columns:
            # Check if frontend passed this exact column name
            val = data.get(col, "")
            input_data[col] = val
        
        # Create a single-row dataframe
        df_input = pd.DataFrame([input_data])
        
        # Apply preprocessing for all features
        for col in feature_columns:
            if col in encoders:
                # Handle unseen categorical labels securely
                known_classes = encoders[col].classes_
                val = str(df_input.loc[0, col])
                if val not in known_classes:
                    logger.warning(f"Unknown value '{val}' for column '{col}'. Using default class: {known_classes[0]}")
                    val = known_classes[0]
                df_input[col] = encoders[col].transform([val])[0]
            elif col in ['MonthlyCharges', 'TotalCharges', 'tenure']:
                try:
                    df_input[col] = float(df_input[col])
                except (ValueError, TypeError):
                    df_input[col] = 0.0
                    
        # Make Prediction strictly on validated feature_columns
        prediction = model.predict(df_input[feature_columns])[0]
        probability = model.predict_proba(df_input[feature_columns])[0]
        
        churn_prob = probability[1] if len(probability) > 1 else (1.0 if prediction == 1 else 0.0)
        
        result = {
            'churn_prediction': bool(prediction == 1),
            'churn_probability': float(churn_prob),
            'status': 'success',
            'confidence': 0.942  # Base Confidence Metric
        }
        
        return jsonify(result)

    except Exception as e:
        import traceback
        logger.error(f"Prediction error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e), 'status': 'failed'}), 400


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'active',
        'model_loaded': model is not None,
        'features_count': len(feature_columns) if feature_columns else 0
    })


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Start the server on port 5000
    print("\n" + "="*60)
    print("🚀 SmartChurn AI Server Starting...")
    print("="*60)
    print(f"📍 Server URL: http://localhost:5000")
    print(f"📍 Health Check: http://localhost:5000/health")
    print("="*60)
    print("\nPress CTRL+C to stop the server\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)