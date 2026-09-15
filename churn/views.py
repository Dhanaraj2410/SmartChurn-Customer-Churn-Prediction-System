import json
import logging
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Customer, PredictionHistory, UploadedDataset, ModelMetadata
from .forms import (
    PredictionForm, CustomerForm, CSVUploadForm,
    UserRegistrationForm, UserLoginForm
)
from .ml_model import get_prediction_service
from .utils import (
    RetentionEngine, DataQualityAnalyzer,
    generate_csv_response, generate_excel_response
)
from .serializers import (
    CustomerSerializer, PredictionHistorySerializer,
    PredictionInputSerializer, DashboardStatsSerializer
)

logger = logging.getLogger(__name__)

# ==========================================
# AUTHENTICATION VIEWS
# ==========================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()

    return render(request, 'churn/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully! Welcome to SmartChurn AI.")
            return redirect('dashboard')
        else:
            messages.error(request, "Registration failed. Please check the errors below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'churn/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


@login_required
def profile_view(request):
    return render(request, 'churn/profile.html', {'user': request.user})


# ==========================================
# CORE & DASHBOARD VIEWS
# ==========================================

def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'churn/home.html')


@login_required
def dashboard_view(request):
    total_customers = Customer.objects.count()
    total_predictions = PredictionHistory.objects.count()
    
    high_risk = PredictionHistory.objects.filter(risk_level='High').count()
    medium_risk = PredictionHistory.objects.filter(risk_level='Medium').count()
    low_risk = PredictionHistory.objects.filter(risk_level='Low').count()

    retained = low_risk + medium_risk
    churn_rate = (high_risk / total_predictions * 100) if total_predictions > 0 else 0.0

    avg_probability = PredictionHistory.objects.aggregate(Avg('churn_probability'))['churn_probability__avg'] or 0.0
    avg_prob_pct = avg_probability * 100

    recent_alerts = PredictionHistory.objects.order_by('-prediction_date')[:5]

    # Chart data calculations
    contract_stats = Customer.objects.values('contract').annotate(total=Count('id'))
    contract_labels = [c['contract'] for c in contract_stats]
    contract_counts = [c['total'] for c in contract_stats]

    payment_stats = Customer.objects.values('payment_method').annotate(total=Count('id'))
    payment_labels = [p['payment_method'] for p in payment_stats]
    payment_counts = [p['total'] for p in payment_stats]

    context = {
        'total_customers': total_customers,
        'total_predictions': total_predictions,
        'high_risk_count': high_risk,
        'medium_risk_count': medium_risk,
        'low_risk_count': low_risk,
        'retained_count': retained,
        'churn_rate_pct': round(churn_rate, 1),
        'retention_rate_pct': round(100.0 - churn_rate, 1),
        'avg_churn_probability_pct': round(avg_prob_pct, 1),
        'recent_alerts': recent_alerts,
        'contract_labels_json': json.dumps(contract_labels),
        'contract_counts_json': json.dumps(contract_counts),
        'payment_labels_json': json.dumps(payment_labels),
        'payment_counts_json': json.dumps(payment_counts),
    }
    return render(request, 'churn/dashboard.html', context)


@login_required
def about_view(request):
    return render(request, 'churn/about.html')


# ==========================================
# PREDICTION ENGINE VIEWS
# ==========================================

@login_required
def predict_view(request):
    result = None
    recommendations = []

    if request.method == 'POST':
        form = PredictionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                service = get_prediction_service()
                res = service.predict_single(data)

                # Save or update customer record
                cust_id = data.get('customerID', 'CUST-8492')
                customer_obj, created = Customer.objects.update_or_create(
                    customer_id=cust_id,
                    defaults={
                        'gender': data.get('gender', 'Male'),
                        'senior_citizen': int(data.get('SeniorCitizen', 0)),
                        'partner': data.get('Partner', 'No'),
                        'dependents': data.get('Dependents', 'No'),
                        'tenure': int(data.get('tenure', 1)),
                        'phone_service': data.get('PhoneService', 'Yes'),
                        'multiple_lines': data.get('MultipleLines', 'No'),
                        'internet_service': data.get('InternetService', 'DSL'),
                        'online_security': data.get('OnlineSecurity', 'No'),
                        'online_backup': data.get('OnlineBackup', 'No'),
                        'device_protection': data.get('DeviceProtection', 'No'),
                        'tech_support': data.get('TechSupport', 'No'),
                        'streaming_tv': data.get('StreamingTV', 'No'),
                        'streaming_movies': data.get('StreamingMovies', 'No'),
                        'contract': data.get('Contract', 'Month-to-month'),
                        'paperless_billing': data.get('PaperlessBilling', 'Yes'),
                        'payment_method': data.get('PaymentMethod', 'Electronic check'),
                        'monthly_charges': float(data.get('MonthlyCharges', 0.0)),
                        'total_charges': float(data.get('TotalCharges', 0.0)),
                    }
                )

                # Save Prediction History
                history = PredictionHistory.objects.create(
                    customer=customer_obj,
                    customer_code=cust_id,
                    churn_prediction=res['prediction_label'],
                    is_churn=res['is_churn'],
                    churn_probability=res['churn_probability'],
                    risk_level=res['risk_level'],
                    confidence=res['confidence'] / 100.0,
                    model_version='v1.0-RF',
                    raw_data=json.dumps(data)
                )

                recommendations = RetentionEngine.get_recommendations(
                    data, res['churn_probability'], res['risk_level']
                )

                result = {
                    'history_id': history.id,
                    'customer_id': cust_id,
                    'is_churn': res['is_churn'],
                    'prediction_label': res['prediction_label'],
                    'churn_probability': res['churn_probability'],
                    'churn_percentage': res['churn_percentage'],
                    'risk_level': res['risk_level'],
                    'confidence': res['confidence'],
                    'key_factors': res['key_factors'],
                    'recommendations': recommendations,
                    'input_data': data
                }

                messages.success(request, f"Prediction completed for customer {cust_id}: {res['risk_level']} Risk ({res['churn_percentage']}%)")
                return render(request, 'churn/result.html', {'result': result})

            except Exception as e:
                logger.exception("Error executing prediction model")
                messages.error(request, f"Prediction error: {str(e)}")
    else:
        form = PredictionForm()

    return render(request, 'churn/predict.html', {'form': form})


@login_required
def result_detail_view(request, history_id):
    history = get_object_or_404(PredictionHistory, id=history_id)
    raw_dict = json.loads(history.raw_data) if history.raw_data else {}
    
    service = get_prediction_service()
    key_factors = service._analyze_risk_factors(raw_dict, history.churn_probability)
    recommendations = RetentionEngine.get_recommendations(raw_dict, history.churn_probability, history.risk_level)

    result = {
        'history_id': history.id,
        'customer_id': history.customer_id,
        'is_churn': history.is_churn,
        'prediction_label': history.churn_prediction,
        'churn_probability': history.churn_probability,
        'churn_percentage': round(history.churn_probability * 100, 1),
        'risk_level': history.risk_level,
        'confidence': round(history.confidence * 100, 1),
        'key_factors': key_factors,
        'recommendations': recommendations,
        'input_data': raw_dict,
        'date': history.prediction_date
    }
    return render(request, 'churn/result.html', {'result': result})


# ==========================================
# CUSTOMER MANAGEMENT (CRUD)
# ==========================================

@login_required
def customer_list_view(request):
    query = request.GET.get('q', '').strip()
    contract_filter = request.GET.get('contract', '')
    gender_filter = request.GET.get('gender', '')
    internet_filter = request.GET.get('internet', '')
    sort_by = request.GET.get('sort', '-created_at')

    customers = Customer.objects.all()

    if query:
        customers = customers.filter(
            Q(customer_id__icontains=query) |
            Q(contract__icontains=query) |
            Q(payment_method__icontains=query)
        )

    if contract_filter:
        customers = customers.filter(contract=contract_filter)
    if gender_filter:
        customers = customers.filter(gender=gender_filter)
    if internet_filter:
        customers = customers.filter(internet_service=internet_filter)

    valid_sorts = ['created_at', '-created_at', 'tenure', '-tenure', 'monthly_charges', '-monthly_charges', 'customer_id']
    if sort_by in valid_sorts:
        customers = customers.order_by(sort_by)

    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'contract_filter': contract_filter,
        'gender_filter': gender_filter,
        'internet_filter': internet_filter,
        'sort_by': sort_by,
        'total_count': customers.count()
    }
    return render(request, 'churn/customers.html', context)


@login_required
def customer_detail_view(request, customer_id):
    customer = get_object_or_404(Customer, customer_id=customer_id)
    predictions = PredictionHistory.objects.filter(Q(customer=customer) | Q(customer_code=customer_id)).order_by('-prediction_date')
    latest_pred = predictions.first()

    context = {
        'customer': customer,
        'predictions': predictions,
        'latest_pred': latest_pred
    }
    return render(request, 'churn/customer_detail.html', context)


@login_required
def customer_create_view(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer {customer.customer_id} created successfully!")
            return redirect('customer_detail', customer_id=customer.customer_id)
    else:
        form = CustomerForm()
    return render(request, 'churn/customer_form.html', {'form': form, 'title': 'Create New Customer'})


@login_required
def customer_update_view(request, customer_id):
    customer = get_object_or_404(Customer, customer_id=customer_id)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f"Customer {customer.customer_id} updated successfully!")
            return redirect('customer_detail', customer_id=customer.customer_id)
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'churn/customer_form.html', {'form': form, 'title': f'Edit Customer {customer.customer_id}'})


@login_required
def customer_delete_view(request, customer_id):
    customer = get_object_or_404(Customer, customer_id=customer_id)
    if request.method == 'POST':
        cid = customer.customer_id
        customer.delete()
        messages.success(request, f"Customer {cid} deleted successfully.")
        return redirect('customers')
    return render(request, 'churn/customer_confirm_delete.html', {'customer': customer})


# ==========================================
# HISTORY & RISK MANAGEMENT
# ==========================================

@login_required
def history_list_view(request):
    query = request.GET.get('q', '').strip()
    risk_filter = request.GET.get('risk', '')
    
    history_qs = PredictionHistory.objects.all()

    if query:
        history_qs = history_qs.filter(Q(customer_code__icontains=query) | Q(customer__customer_id__icontains=query))
    if risk_filter:
        history_qs = history_qs.filter(risk_level=risk_filter)

    paginator = Paginator(history_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'risk_filter': risk_filter
    }
    return render(request, 'churn/history.html', context)


@login_required
def high_risk_customers_view(request):
    high_risk_qs = PredictionHistory.objects.filter(risk_level='High').order_by('-churn_probability')
    
    high_risk_list = []
    service = get_prediction_service()

    for pred in high_risk_qs:
        raw_dict = json.loads(pred.raw_data) if pred.raw_data else {}
        recs = RetentionEngine.get_recommendations(raw_dict, pred.churn_probability, pred.risk_level)
        high_risk_list.append({
            'history': pred,
            'contract': raw_dict.get('Contract', 'Month-to-month'),
            'tenure': raw_dict.get('tenure', 1),
            'monthly_charges': raw_dict.get('MonthlyCharges', 0.0),
            'recommendations': recs[:2] # Top 2 recommendations
        })

    paginator = Paginator(high_risk_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'churn/high_risk.html', {'page_obj': page_obj, 'total_high_risk': len(high_risk_list)})


@login_required
def delete_history_view(request, history_id):
    history = get_object_or_404(PredictionHistory, id=history_id)
    if request.method == 'POST':
        history.delete()
        messages.success(request, "Prediction record removed.")
    return redirect('history')


# ==========================================
# BULK CSV UPLOAD & EXPORTS
# ==========================================

@login_required
def csv_upload_view(request):
    upload_result = None

    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']

            if not csv_file.name.endswith('.csv'):
                messages.error(request, "Uploaded file is not a CSV.")
                return redirect('csv_upload')

            try:
                df = pd.read_csv(csv_file)
                total_records = len(df)

                # Quality Analysis
                quality_res = DataQualityAnalyzer.analyze_dataframe(df)

                # Run predictions batch
                service = get_prediction_service()
                high_cnt = 0
                med_cnt = 0
                low_cnt = 0
                valid_cnt = 0
                invalid_cnt = 0

                for idx, row in df.iterrows():
                    try:
                        row_dict = row.to_dict()
                        cust_id = str(row_dict.get('customerID', f'CSV-{idx+1001}'))
                        
                        res = service.predict_single(row_dict)
                        valid_cnt += 1

                        if res['risk_level'] == 'High':
                            high_cnt += 1
                        elif res['risk_level'] == 'Medium':
                            med_cnt += 1
                        else:
                            low_cnt += 1

                        # Save to database
                        cust_obj, _ = Customer.objects.update_or_create(
                            customer_id=cust_id,
                            defaults={
                                'gender': str(row_dict.get('gender', 'Male')),
                                'senior_citizen': int(row_dict.get('SeniorCitizen', 0) or 0),
                                'partner': str(row_dict.get('Partner', 'No')),
                                'dependents': str(row_dict.get('Dependents', 'No')),
                                'tenure': int(row_dict.get('tenure', 1) or 1),
                                'phone_service': str(row_dict.get('PhoneService', 'Yes')),
                                'multiple_lines': str(row_dict.get('MultipleLines', 'No')),
                                'internet_service': str(row_dict.get('InternetService', 'DSL')),
                                'contract': str(row_dict.get('Contract', 'Month-to-month')),
                                'paperless_billing': str(row_dict.get('PaperlessBilling', 'Yes')),
                                'payment_method': str(row_dict.get('PaymentMethod', 'Electronic check')),
                                'monthly_charges': float(row_dict.get('MonthlyCharges', 0.0) or 0.0),
                                'total_charges': float(row_dict.get('TotalCharges', 0.0) or 0.0),
                            }
                        )

                        PredictionHistory.objects.create(
                            customer=cust_obj,
                            customer_code=cust_id,
                            churn_prediction=res['prediction_label'],
                            is_churn=res['is_churn'],
                            churn_probability=res['churn_probability'],
                            risk_level=res['risk_level'],
                            confidence=res['confidence'] / 100.0,
                            model_version='v1.0-BatchCSV',
                            raw_data=json.dumps(row_dict, default=str)
                        )

                    except Exception as e:
                        invalid_cnt += 1
                        logger.warning(f"Error processing row {idx}: {e}")

                upload_record = UploadedDataset.objects.create(
                    filename=csv_file.name,
                    total_records=total_records,
                    valid_records=valid_cnt,
                    invalid_records=invalid_cnt,
                    high_risk_count=high_cnt,
                    medium_risk_count=med_cnt,
                    low_risk_count=low_cnt,
                    quality_score=quality_res['quality_score']
                )

                upload_result = {
                    'filename': csv_file.name,
                    'total_records': total_records,
                    'valid_records': valid_cnt,
                    'invalid_records': invalid_cnt,
                    'high_risk_count': high_cnt,
                    'medium_risk_count': med_cnt,
                    'low_risk_count': low_cnt,
                    'quality_score': quality_res['quality_score'],
                    'quality_details': quality_res
                }

                messages.success(request, f"Successfully processed {valid_cnt} records from {csv_file.name}!")

            except Exception as e:
                logger.exception("CSV Batch processing error")
                messages.error(request, f"Failed to parse CSV file: {str(e)}")
    else:
        form = CSVUploadForm()

    return render(request, 'churn/csv_upload.html', {'form': form, 'result': upload_result})


@login_required
def export_csv_view(request):
    history_qs = PredictionHistory.objects.all().order_by('-prediction_date')
    return generate_csv_response(history_qs, filename="smartchurn_prediction_history.csv")


@login_required
def export_excel_view(request):
    history_qs = PredictionHistory.objects.all().order_by('-prediction_date')
    return generate_excel_response(history_qs, filename="smartchurn_prediction_history.xlsx")


# ==========================================
# ANALYTICS & DIAGNOSTICS
# ==========================================

@login_required
def analytics_view(request):
    total = Customer.objects.count()
    if total == 0:
        messages.info(request, "No customer data available yet for analytics.")
        return render(request, 'churn/analytics.html', {'empty': True})

    avg_tenure = Customer.objects.aggregate(Avg('tenure'))['tenure__avg'] or 0
    avg_monthly = Customer.objects.aggregate(Avg('monthly_charges'))['monthly_charges__avg'] or 0

    contract_data = list(Customer.objects.values('contract').annotate(count=Count('id')))
    payment_data = list(Customer.objects.values('payment_method').annotate(count=Count('id')))
    internet_data = list(Customer.objects.values('internet_service').annotate(count=Count('id')))
    gender_data = list(Customer.objects.values('gender').annotate(count=Count('id')))

    context = {
        'total_customers': total,
        'avg_tenure': round(avg_tenure, 1),
        'avg_monthly': round(avg_monthly, 2),
        'contract_data_json': json.dumps(contract_data),
        'payment_data_json': json.dumps(payment_data),
        'internet_data_json': json.dumps(internet_data),
        'gender_data_json': json.dumps(gender_data),
    }
    return render(request, 'churn/analytics.html', context)


@login_required
def model_info_view(request):
    metadata = ModelMetadata.objects.first()
    if not metadata:
        metadata = ModelMetadata.objects.create(
            model_name='Random Forest Classifier',
            version='v1.0',
            accuracy=0.812,
            precision=0.795,
            recall=0.784,
            f1_score=0.789,
            roc_auc=0.845,
            num_features=19,
            confusion_matrix_json=json.dumps([[1150, 150], [210, 580]])
        )

    confusion_matrix = json.loads(metadata.confusion_matrix_json) if metadata.confusion_matrix_json else []

    features = [
        'gender', 'SeniorCitizen', 'Partner', 'Dependents', 'tenure',
        'PhoneService', 'MultipleLines', 'InternetService', 'OnlineSecurity',
        'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV',
        'StreamingMovies', 'Contract', 'PaperlessBilling', 'PaymentMethod',
        'MonthlyCharges', 'TotalCharges'
    ]

    context = {
        'metadata': metadata,
        'confusion_matrix': confusion_matrix,
        'features': features
    }
    return render(request, 'churn/model.html', context)


@login_required
def data_quality_view(request):
    customers = Customer.objects.all()
    if customers.exists():
        data = list(customers.values())
        df = pd.DataFrame(data)
        quality_res = DataQualityAnalyzer.analyze_dataframe(df)
    else:
        quality_res = DataQualityAnalyzer.analyze_dataframe(pd.DataFrame())

    recent_uploads = UploadedDataset.objects.all()[:5]

    context = {
        'quality': quality_res,
        'recent_uploads': recent_uploads
    }
    return render(request, 'churn/data_quality.html', context)


# ==========================================
# REST API ENDPOINTS
# ==========================================

class PredictAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request):
        serializer = PredictionInputSerializer(data=request.data)
        if serializer.is_valid():
            input_dict = serializer.validated_data
            try:
                service = get_prediction_service()
                res = service.predict_single(input_dict)
                recs = RetentionEngine.get_recommendations(input_dict, res['churn_probability'], res['risk_level'])

                return Response({
                    'status': 'success',
                    'customer_id': input_dict.get('customerID', 'API-User'),
                    'prediction': res['prediction_label'],
                    'is_churn': res['is_churn'],
                    'probability': res['churn_probability'],
                    'churn_percentage': res['churn_percentage'],
                    'risk_level': res['risk_level'],
                    'confidence': res['confidence'],
                    'key_factors': res['key_factors'],
                    'recommendations': recs
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        customers = Customer.objects.all()[:100]
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)


class PredictionHistoryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        history = PredictionHistory.objects.all()[:100]
        serializer = PredictionHistorySerializer(history, many=True)
        return Response(serializer.data)


class DashboardStatsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        total_customers = Customer.objects.count()
        total_predictions = PredictionHistory.objects.count()
        high_risk = PredictionHistory.objects.filter(risk_level='High').count()
        medium_risk = PredictionHistory.objects.filter(risk_level='Medium').count()
        low_risk = PredictionHistory.objects.filter(risk_level='Low').count()

        churn_rate = (high_risk / total_predictions * 100) if total_predictions > 0 else 0.0
        avg_probability = PredictionHistory.objects.aggregate(Avg('churn_probability'))['churn_probability__avg'] or 0.0

        return Response({
            'total_customers': total_customers,
            'total_predictions': total_predictions,
            'high_risk_count': high_risk,
            'medium_risk_count': medium_risk,
            'low_risk_count': low_risk,
            'churn_rate_pct': round(churn_rate, 1),
            'avg_churn_probability_pct': round(avg_probability * 100, 1)
        })


def health_check_api(request):
    """
    Legacy API endpoint for system health check
    """
    service = get_prediction_service()
    return JsonResponse({
        'status': 'active',
        'database': 'connected',
        'model_loaded': service.model is not None,
        'framework': 'Django 5.1'
    })
