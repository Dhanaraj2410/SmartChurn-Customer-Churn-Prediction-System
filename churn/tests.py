import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.template.context import Context, RequestContext

# Python 3.14 Django Context copy compatibility fix
def _context_copy(self):
    duplicate = Context()
    duplicate.dicts = getattr(self, 'dicts', [])[:]
    return duplicate

Context.__copy__ = _context_copy
RequestContext.__copy__ = _context_copy

from .models import Customer, PredictionHistory, UploadedDataset, ModelMetadata
from .ml_model import get_prediction_service
from .utils import RetentionEngine, DataQualityAnalyzer


class SmartChurnModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.customer = Customer.objects.create(
            customer_id='CUST-TEST-01',
            gender='Male',
            senior_citizen=0,
            partner='No',
            dependents='No',
            tenure=12,
            phone_service='Yes',
            multiple_lines='No',
            internet_service='DSL',
            contract='Month-to-month',
            monthly_charges=65.50,
            total_charges=786.00
        )

    def test_customer_creation(self):
        self.assertEqual(self.customer.customer_id, 'CUST-TEST-01')
        self.assertEqual(str(self.customer), 'Customer CUST-TEST-01')

    def test_prediction_history_creation(self):
        history = PredictionHistory.objects.create(
            customer=self.customer,
            customer_code=self.customer.customer_id,
            churn_prediction='Churn',
            is_churn=True,
            churn_probability=0.82,
            risk_level='High',
            confidence=0.91,
            model_version='v1.0-Test'
        )
        self.assertTrue(history.is_churn)
        self.assertEqual(history.risk_level, 'High')


class SmartChurnMLServiceTests(TestCase):
    def test_prediction_service_single(self):
        service = get_prediction_service()
        input_data = {
            'customerID': 'CUST-ML-01',
            'gender': 'Female',
            'SeniorCitizen': 0,
            'Partner': 'No',
            'Dependents': 'No',
            'tenure': 2,
            'PhoneService': 'Yes',
            'MultipleLines': 'No',
            'InternetService': 'Fiber optic',
            'OnlineSecurity': 'No',
            'OnlineBackup': 'No',
            'DeviceProtection': 'No',
            'TechSupport': 'No',
            'StreamingTV': 'Yes',
            'StreamingMovies': 'Yes',
            'Contract': 'Month-to-month',
            'PaperlessBilling': 'Yes',
            'PaymentMethod': 'Electronic check',
            'MonthlyCharges': 95.0,
            'TotalCharges': 190.0
        }
        res = service.predict_single(input_data)
        self.assertIn('is_churn', res)
        self.assertIn('churn_probability', res)
        self.assertIn('risk_level', res)
        self.assertIn(res['risk_level'], ['Low', 'Medium', 'High'])

    def test_retention_engine(self):
        data = {'Contract': 'Month-to-month', 'MonthlyCharges': 85.0, 'tenure': 3}
        recs = RetentionEngine.get_recommendations(data, churn_probability=0.85, risk_level='High')
        self.assertTrue(len(recs) > 0)


class SmartChurnViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.customer = Customer.objects.create(
            customer_id='CUST-VIEW-01',
            contract='Month-to-month',
            monthly_charges=75.0
        )

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_login_and_dashboard_access(self):
        response = self.client.post(reverse('login'), {'username': 'testuser', 'password': 'password123'})
        self.assertRedirects(response, reverse('dashboard'))

        dashboard_res = self.client.get(reverse('dashboard'))
        self.assertEqual(dashboard_res.status_code, 200)

    def test_predict_form_post(self):
        self.client.login(username='testuser', password='password123')
        data = {
            'customerID': 'CUST-FORM-01',
            'gender': 'Male',
            'SeniorCitizen': 0,
            'Partner': 'No',
            'Dependents': 'No',
            'tenure': 12,
            'PhoneService': 'Yes',
            'MultipleLines': 'No',
            'InternetService': 'DSL',
            'OnlineSecurity': 'No',
            'OnlineBackup': 'No',
            'DeviceProtection': 'No',
            'TechSupport': 'No',
            'StreamingTV': 'No',
            'StreamingMovies': 'No',
            'Contract': 'Month-to-month',
            'PaperlessBilling': 'Yes',
            'PaymentMethod': 'Electronic check',
            'MonthlyCharges': 55.0,
            'TotalCharges': 660.0
        }
        response = self.client.post(reverse('predict'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PredictionHistory.objects.filter(customer_code='CUST-FORM-01').exists())


class SmartChurnAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='apiuser', password='password123')
        self.client.force_login(self.user)

    def test_api_predict(self):
        url = reverse('api_predict')
        payload = {
            'customerID': 'API-CUST-99',
            'tenure': 12,
            'MonthlyCharges': 75.5,
            'Contract': 'Month-to-month'
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['status'], 'success')
        self.assertIn('risk_level', json_data)

    def test_health_api(self):
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'active')
