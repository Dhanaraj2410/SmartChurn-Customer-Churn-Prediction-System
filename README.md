<<<<<<< HEAD
# SmartChurn – Customer Churn Prediction System


An AI-powered Machine Learning web application designed to predict whether a customer is likely to leave a service. By analyzing customer behavior and service usage patterns, this system identifies high-risk customers, enabling businesses to take proactive measures and improve customer retention.


## ✨ Features 
* **Machine Learning Prediction:** Accurate customer churn forecasting.
* **Random Forest Model:** Utilizes a robust classification algorithm for high accuracy.
* **Real-Time Processing:** Instantly processes inputs to deliver immediate prediction results.
* **Interactive Dashboard:** A responsive, user-friendly web interface for seamless data entry.
* **Customer Behavior Analysis:** Evaluates key metrics to determine churn probability.
* **Flask Backend:** Lightweight and efficient server integration.

## 🛠️ Technologies Used
* **Backend:** Python, Flask
* **Machine Learning:** Scikit-learn, Pandas, NumPy
* **Frontend:** HTML, CSS, JavaScript

## ⚙️ Machine Learning Workflow
1.  **Data Collection:** Gathering customer demographic and service data.
2.  **Data Preprocessing:** Cleaning data, handling missing values, and scaling features.
3.  **Feature Engineering:** Encoding categorical variables and selecting key predictors.
4.  **Model Training:** Training the Random Forest Classifier on historical churn data.
5.  **Churn Prediction:** Generating binary outcomes based on new inputs.
6.  **Web Deployment:** Serving the model via a Flask web application.

## 🤖 Algorithm

**Random Forest Classifier**

The system uses an ensemble learning method that constructs a multitude of decision trees at training time. It analyzes complex customer behavior patterns and outputs the mode of the classes (churn or stay) of the individual trees, providing a highly accurate and stable prediction.

Built an AI-driven customer churn predictor using Random Forest and Scikit-learn.

Engineered features from customer tenure, billing, and service usage data.

Deployed a real-time Flask web application for instant churn risk assessment.

=======
# SmartChurn AI – Enterprise Customer Churn Prediction System (Django Version)

SmartChurn AI is an enterprise customer churn prediction and retention management web application built using **Python**, **Django 5.1**, **Pandas**, **NumPy**, **Scikit-learn**, **Django REST Framework**, and **Chart.js**.

The application predicts customer churn probabilities based on demographic, account billing, contract type, and service telemetry.

---

## Key Features

1. **Random Forest Machine Learning Pipeline**: Preserves scikit-learn model inference with probability calculation (`predict_proba()`), confidence scoring, and key risk factor extraction.
2. **Interactive Retention Dashboard**: Dynamic KPI statistics, Chart.js doughuts and bar charts for churn distribution, contract types, and payment methods.
3. **Single Customer ML Prediction**: Multi-section telemetry form returning risk levels (Low 0–30%, Medium 31–60%, High 61–100%), risk indicators, and printable PDF reports.
4. **Rule-Based Retention Recommendation System**: Automated action plan generation recommending contract switches, pricing reviews, tech support bundles, or onboarding calls based on risk profile.
5. **Customer Directory Management**: Full CRUD operations for customer profiles with multi-criteria search, filtering, sorting, and pagination.
6. **Bulk CSV Telemetry Processing**: Batch processing of customer CSV files, data quality analysis (Data Quality Score %), and batch database recording.
7. **Prediction History & Risk Logs**: Detailed history table with export options to CSV and Excel.
8. **High Risk Accounts View**: Dedicated view sorting customers by highest churn probability for immediate intervention.
9. **Data Quality Diagnostics**: Automated quality inspection calculating completeness, duplicate counts, and schema health.
10. **REST APIs & Admin Panel**: Secure REST endpoints (`/api/predict/`, `/api/customers/`, `/api/predictions/`, `/api/dashboard/`) and Django Admin interface.

---

## Technology Stack

- **Backend**: Python 3.14, Django 5.1, Django REST Framework
- **Machine Learning**: Scikit-learn (Random Forest Classifier), Pandas, NumPy, Joblib
- **Frontend**: HTML5, Tailwind CSS, FontAwesome 6, Chart.js, jsPDF
- **Database**: SQLite (Default) / SQL Server / PostgreSQL support
- **Exporting**: OpenPyXL, CSV

---

## Architecture Overview

```text
customer_churn/
│
├── manage.py
│
├── smartchurn/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── churn/
│   ├── migrations/
│   ├── templates/
│   │   └── churn/
│   │       ├── base.html
│   │       ├── home.html
│   │       ├── dashboard.html
│   │       ├── predict.html
│   │       ├── result.html
│   │       ├── customers.html
│   │       ├── customer_detail.html
│   │       ├── customer_form.html
│   │       ├── history.html
│   │       ├── high_risk.html
│   │       ├── csv_upload.html
│   │       ├── analytics.html
│   │       ├── model.html
│   │       ├── data_quality.html
│   │       ├── about.html
│   │       ├── login.html
│   │       └── register.html
│   │
│   ├── static/
│   │   └── churn/
│   │       ├── css/styles.css
│   │       └── js/main.js
│   │
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   ├── ml_model.py
│   ├── utils.py
│   ├── serializers.py
│   └── tests.py
│
├── ml/
│   ├── model/
│   │   ├── model.pkl
│   │   └── metadata.json
│   └── training/
│       └── train_model.py
│
├── data/
│   └── customer_churn.csv
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Quick Start & Installation

### 1. Clone & Setup Virtual Environment

```bash
git clone <repository-url>
cd customer_churn

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Mac/Linux)
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Admin Superuser

```bash
python manage.py createsuperuser
```

### 5. Run Django Server

```bash
python manage.py runserver
```

Open your browser and navigate to:
```text
http://127.0.0.1:8000/
```

---

## Machine Learning Training Script

To retrain the Random Forest model and update performance metrics:

```bash
python ml/training/train_model.py
```

---

## Running Automated Tests

```bash
python manage.py test churn
```

---

## REST API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/predict/` | `POST` | Execute single ML prediction |
| `/api/customers/` | `GET` | Retrieve list of customers |
| `/api/predictions/` | `GET` | Retrieve prediction history logs |
| `/api/dashboard/` | `GET` | Retrieve summary dashboard metrics |
| `/health/` | `GET` | Health check endpoint |

### Example API Request (`/api/predict/`)

```json
POST /api/predict/
Content-Type: application/json

{
    "customerID": "API-CUST-88",
    "tenure": 12,
    "MonthlyCharges": 85.5,
    "Contract": "Month-to-month",
    "InternetService": "Fiber optic"
}
```

---

## License

Designed and developed by Dhanaraj. Enterprise Customer Retention System.
>>>>>>> 5e45e27 (docs & cleanup: update requirements, README documentation, and remove legacy Flask entry point)
