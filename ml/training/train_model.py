import os
import json
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_FILE = BASE_DIR / 'data' / 'customer_churn.csv'
MODEL_DIR = BASE_DIR / 'ml' / 'model'
MODEL_FILE = MODEL_DIR / 'model.pkl'
METADATA_FILE = MODEL_DIR / 'metadata.json'

def train():
    print(f"Loading training dataset from {DATA_FILE}...")
    df = pd.read_csv(DATA_FILE)

    # Clean TotalCharges
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
    df['TotalCharges'] = df['TotalCharges'].fillna(df['TotalCharges'].mean())

    # Map Target
    if 'Churn' in df.columns:
        y = df['Churn'].map({'Yes': 1, 'No': 0, 1: 1, 0: 0})
        X_raw = df.drop(columns=['Churn'])
    else:
        raise ValueError("Target column 'Churn' not found in dataset.")

    if 'customerID' in X_raw.columns:
        X_raw = X_raw.drop(columns=['customerID'])

    feature_names = X_raw.columns.tolist()
    encoders = {}

    # Encoding
    X_encoded = X_raw.copy()
    for col in feature_names:
        if not pd.api.types.is_numeric_dtype(X_encoded[col]):
            le = LabelEncoder()
            X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
            encoders[col] = le


    # Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_encoded, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Training Random Forest Classifier on {len(X_train)} samples...")
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)

    # Evaluation
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred))
    rec = float(recall_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred))
    auc = float(roc_auc_score(y_test, y_prob))
    cm = confusion_matrix(y_test, y_pred).tolist()

    print("Model Training & Evaluation Results:")
    print(f"  Accuracy:  {acc*100:.2f}%")
    print(f"  Precision: {prec*100:.2f}%")
    print(f"  Recall:    {rec*100:.2f}%")
    print(f"  F1 Score:  {f1*100:.2f}%")
    print(f"  ROC-AUC:   {auc:.4f}")

    os.makedirs(MODEL_DIR, exist_ok=True)

    # Save Model
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model saved to {MODEL_FILE}")

    # Save Metadata
    metadata = {
        'model_name': 'Random Forest Classifier',
        'version': 'v1.0-RF',
        'accuracy': acc,
        'precision': prec,
        'recall': rec,
        'f1_score': f1,
        'roc_auc': auc,
        'num_features': len(feature_names),
        'features': feature_names,
        'confusion_matrix': cm
    }

    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to {METADATA_FILE}")

if __name__ == '__main__':
    train()
