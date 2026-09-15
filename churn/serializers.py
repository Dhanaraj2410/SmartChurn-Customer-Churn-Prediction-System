from rest_framework import serializers
from .models import Customer, PredictionHistory, UploadedDataset, ModelMetadata

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class PredictionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionHistory
        fields = '__all__'


class PredictionInputSerializer(serializers.Serializer):
    customerID = serializers.CharField(default='CUST-1001')
    gender = serializers.CharField(default='Male')
    SeniorCitizen = serializers.IntegerField(default=0)
    Partner = serializers.CharField(default='No')
    Dependents = serializers.CharField(default='No')
    tenure = serializers.IntegerField(default=12)
    PhoneService = serializers.CharField(default='Yes')
    MultipleLines = serializers.CharField(default='No')
    InternetService = serializers.CharField(default='Fiber optic')
    OnlineSecurity = serializers.CharField(default='No')
    OnlineBackup = serializers.CharField(default='No')
    DeviceProtection = serializers.CharField(default='No')
    TechSupport = serializers.CharField(default='No')
    StreamingTV = serializers.CharField(default='Yes')
    StreamingMovies = serializers.CharField(default='Yes')
    Contract = serializers.CharField(default='Month-to-month')
    PaperlessBilling = serializers.CharField(default='Yes')
    PaymentMethod = serializers.CharField(default='Electronic check')
    MonthlyCharges = serializers.FloatField(default=85.50)
    TotalCharges = serializers.FloatField(default=1026.00)


class DashboardStatsSerializer(serializers.Serializer):
    total_customers = serializers.IntegerField()
    total_predictions = serializers.IntegerField()
    high_risk_count = serializers.IntegerField()
    medium_risk_count = serializers.IntegerField()
    low_risk_count = serializers.IntegerField()
    churn_rate_pct = serializers.FloatField()
    avg_churn_probability_pct = serializers.FloatField()
