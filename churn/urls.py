from django.urls import path
from . import views

urlpatterns = [
    # Auth & Base
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('about/', views.about_view, name='about'),

    # Main Application Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # ML Prediction
    path('predict/', views.predict_view, name='predict'),
    path('result/<int:history_id>/', views.result_detail_view, name='result_detail'),

    # Customer Management (CRUD)
    path('customers/', views.customer_list_view, name='customers'),
    path('customers/add/', views.customer_create_view, name='customer_create'),
    path('customers/<str:customer_id>/', views.customer_detail_view, name='customer_detail'),
    path('customers/<str:customer_id>/edit/', views.customer_update_view, name='customer_update'),
    path('customers/<str:customer_id>/delete/', views.customer_delete_view, name='customer_delete'),

    # Prediction History & Risk Management
    path('history/', views.history_list_view, name='history'),
    path('history/<int:history_id>/delete/', views.delete_history_view, name='delete_history'),
    path('high-risk/', views.high_risk_customers_view, name='high_risk'),

    # CSV Upload & Export Features
    path('csv-upload/', views.csv_upload_view, name='csv_upload'),
    path('export/csv/', views.export_csv_view, name='export_csv'),
    path('export/excel/', views.export_excel_view, name='export_excel'),

    # Analytics & Model Information
    path('analytics/', views.analytics_view, name='analytics'),
    path('model-info/', views.model_info_view, name='model_info'),
    path('data-quality/', views.data_quality_view, name='data_quality'),

    # Health & REST API Endpoints
    path('health/', views.health_check_api, name='health'),
    path('api/predict/', views.PredictAPIView.as_view(), name='api_predict'),
    path('api/customers/', views.CustomerListAPIView.as_view(), name='api_customers'),
    path('api/predictions/', views.PredictionHistoryAPIView.as_view(), name='api_predictions'),
    path('api/dashboard/', views.DashboardStatsAPIView.as_view(), name='api_dashboard'),
]
