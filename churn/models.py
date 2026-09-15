from django.db import models

class Customer(models.Model):
    customer_id = models.CharField(max_length=100, unique=True, verbose_name="Customer ID")
    gender = models.CharField(max_length=20, default='Male')
    senior_citizen = models.IntegerField(default=0, verbose_name="Senior Citizen (0 or 1)")
    partner = models.CharField(max_length=10, default='No')
    dependents = models.CharField(max_length=10, default='No')
    tenure = models.IntegerField(default=1, verbose_name="Tenure (Months)")
    phone_service = models.CharField(max_length=10, default='Yes')
    multiple_lines = models.CharField(max_length=30, default='No')
    internet_service = models.CharField(max_length=30, default='DSL')
    online_security = models.CharField(max_length=30, default='No')
    online_backup = models.CharField(max_length=30, default='No')
    device_protection = models.CharField(max_length=30, default='No')
    tech_support = models.CharField(max_length=30, default='No')
    streaming_tv = models.CharField(max_length=30, default='No')
    streaming_movies = models.CharField(max_length=30, default='No')
    contract = models.CharField(max_length=30, default='Month-to-month')
    paperless_billing = models.CharField(max_length=10, default='Yes')
    payment_method = models.CharField(max_length=50, default='Electronic check')
    monthly_charges = models.FloatField(default=0.0, verbose_name="Monthly Charges ($)")
    total_charges = models.FloatField(default=0.0, verbose_name="Total Charges ($)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Customer {self.customer_id}"

class PredictionHistory(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='predictions')
    customer_code = models.CharField(max_length=100, default='Unknown')
    churn_prediction = models.CharField(max_length=20, default='Safe') # 'Churn' or 'Safe'
    is_churn = models.BooleanField(default=False)
    churn_probability = models.FloatField(default=0.0) # 0.0 to 1.0
    risk_level = models.CharField(max_length=20, default='Low') # 'Low', 'Medium', 'High'
    confidence = models.FloatField(default=0.0)
    model_version = models.CharField(max_length=50, default='v1.0')
    raw_data = models.TextField(blank=True, null=True) # JSON string of inputs
    prediction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-prediction_date']
        verbose_name_plural = "Prediction Histories"

    @property
    def customer_id(self):
        if self.customer and self.customer.customer_id:
            return self.customer.customer_id
        return self.customer_code

    def __str__(self):
        return f"{self.customer_id} - {self.churn_prediction} ({self.churn_probability*100:.1f}%)"


class UploadedDataset(models.Model):
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    total_records = models.IntegerField(default=0)
    valid_records = models.IntegerField(default=0)
    invalid_records = models.IntegerField(default=0)
    high_risk_count = models.IntegerField(default=0)
    medium_risk_count = models.IntegerField(default=0)
    low_risk_count = models.IntegerField(default=0)
    quality_score = models.FloatField(default=100.0)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.filename} ({self.uploaded_at.strftime('%Y-%m-%d %H:%M')})"

class ModelMetadata(models.Model):
    model_name = models.CharField(max_length=100, default='Random Forest Classifier')
    version = models.CharField(max_length=50, default='v1.0')
    accuracy = models.FloatField(default=0.0)
    precision = models.FloatField(default=0.0)
    recall = models.FloatField(default=0.0)
    f1_score = models.FloatField(default=0.0)
    roc_auc = models.FloatField(default=0.0)
    num_features = models.IntegerField(default=19)
    training_date = models.DateTimeField(auto_now_add=True)
    confusion_matrix_json = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-training_date']

    def __str__(self):
        return f"{self.model_name} {self.version} (Acc: {self.accuracy*100:.1f}%)"
