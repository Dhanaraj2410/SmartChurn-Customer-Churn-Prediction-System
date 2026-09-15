from django.contrib import admin
from .models import Customer, PredictionHistory, UploadedDataset, ModelMetadata

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'gender', 'contract', 'payment_method', 'monthly_charges', 'total_charges', 'tenure', 'created_at')
    list_filter = ('contract', 'gender', 'internet_service', 'payment_method')
    search_fields = ('customer_id', 'contract', 'payment_method')
    ordering = ('-created_at',)


@admin.register(PredictionHistory)
class PredictionHistoryAdmin(admin.ModelAdmin):
    list_display = ('customer_code', 'churn_prediction', 'risk_level', 'churn_probability', 'confidence', 'prediction_date')
    list_filter = ('risk_level', 'churn_prediction', 'model_version')
    search_fields = ('customer_code', 'churn_prediction', 'risk_level')
    readonly_fields = ('prediction_date',)
    ordering = ('-prediction_date',)


@admin.register(UploadedDataset)
class UploadedDatasetAdmin(admin.ModelAdmin):
    list_display = ('filename', 'uploaded_at', 'total_records', 'valid_records', 'quality_score', 'high_risk_count')
    readonly_fields = ('uploaded_at',)


@admin.register(ModelMetadata)
class ModelMetadataAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'version', 'accuracy', 'precision', 'recall', 'f1_score', 'roc_auc', 'training_date')
    readonly_fields = ('training_date',)
