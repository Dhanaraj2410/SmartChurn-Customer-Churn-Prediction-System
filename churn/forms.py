from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Customer

GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female')]
YES_NO_CHOICES = [('Yes', 'Yes'), ('No', 'No')]
SENIOR_CHOICES = [(0, 'No'), (1, 'Yes')]

MULTIPLE_LINES_CHOICES = [('No', 'No'), ('Yes', 'Yes'), ('No phone service', 'No phone service')]
INTERNET_SERVICE_CHOICES = [('DSL', 'DSL'), ('Fiber optic', 'Fiber optic'), ('No', 'No')]
SERVICE_ADDON_CHOICES = [('No', 'No'), ('Yes', 'Yes'), ('No internet service', 'No internet service')]
CONTRACT_CHOICES = [('Month-to-month', 'Month-to-month'), ('One year', 'One year'), ('Two year', 'Two year')]
PAYMENT_METHOD_CHOICES = [
    ('Electronic check', 'Electronic check'),
    ('Mailed check', 'Mailed check'),
    ('Bank transfer (automatic)', 'Bank transfer (automatic)'),
    ('Credit card (automatic)', 'Credit card (automatic)'),
]

class PredictionForm(forms.Form):
    customerID = forms.CharField(
        max_length=100,
        initial='CUST-8492',
        label='Customer ID',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CUST-8492'})
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        initial='Male',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    SeniorCitizen = forms.ChoiceField(
        choices=SENIOR_CHOICES,
        initial=0,
        label='Senior Citizen',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    Partner = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        initial='No',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    Dependents = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        initial='No',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tenure = forms.IntegerField(
        min_value=0,
        max_value=100,
        initial=12,
        label='Tenure (Months)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100})
    )
    PhoneService = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        initial='Yes',
        label='Phone Service',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    MultipleLines = forms.ChoiceField(
        choices=MULTIPLE_LINES_CHOICES,
        initial='No',
        label='Multiple Lines',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    InternetService = forms.ChoiceField(
        choices=INTERNET_SERVICE_CHOICES,
        initial='Fiber optic',
        label='Internet Service',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    OnlineSecurity = forms.ChoiceField(
        choices=SERVICE_ADDON_CHOICES,
        initial='No',
        label='Online Security',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    OnlineBackup = forms.ChoiceField(
        choices=SERVICE_ADDON_CHOICES,
        initial='No',
        label='Online Backup',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    DeviceProtection = forms.ChoiceField(
        choices=SERVICE_ADDON_CHOICES,
        initial='No',
        label='Device Protection',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    TechSupport = forms.ChoiceField(
        choices=SERVICE_ADDON_CHOICES,
        initial='No',
        label='Tech Support',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    StreamingTV = forms.ChoiceField(
        choices=SERVICE_ADDON_CHOICES,
        initial='Yes',
        label='Streaming TV',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    StreamingMovies = forms.ChoiceField(
        choices=SERVICE_ADDON_CHOICES,
        initial='Yes',
        label='Streaming Movies',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    Contract = forms.ChoiceField(
        choices=CONTRACT_CHOICES,
        initial='Month-to-month',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    PaperlessBilling = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        initial='Yes',
        label='Paperless Billing',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    PaymentMethod = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        initial='Electronic check',
        label='Payment Method',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    MonthlyCharges = forms.FloatField(
        min_value=0.0,
        initial=85.50,
        label='Monthly Charges ($)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    TotalCharges = forms.FloatField(
        min_value=0.0,
        initial=1026.00,
        label='Total Charges ($)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        widgets = {
            'customer_id': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(choices=GENDER_CHOICES, attrs={'class': 'form-select'}),
            'senior_citizen': forms.Select(choices=SENIOR_CHOICES, attrs={'class': 'form-select'}),
            'partner': forms.Select(choices=YES_NO_CHOICES, attrs={'class': 'form-select'}),
            'dependents': forms.Select(choices=YES_NO_CHOICES, attrs={'class': 'form-select'}),
            'tenure': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'phone_service': forms.Select(choices=YES_NO_CHOICES, attrs={'class': 'form-select'}),
            'multiple_lines': forms.Select(choices=MULTIPLE_LINES_CHOICES, attrs={'class': 'form-select'}),
            'internet_service': forms.Select(choices=INTERNET_SERVICE_CHOICES, attrs={'class': 'form-select'}),
            'online_security': forms.Select(choices=SERVICE_ADDON_CHOICES, attrs={'class': 'form-select'}),
            'online_backup': forms.Select(choices=SERVICE_ADDON_CHOICES, attrs={'class': 'form-select'}),
            'device_protection': forms.Select(choices=SERVICE_ADDON_CHOICES, attrs={'class': 'form-select'}),
            'tech_support': forms.Select(choices=SERVICE_ADDON_CHOICES, attrs={'class': 'form-select'}),
            'streaming_tv': forms.Select(choices=SERVICE_ADDON_CHOICES, attrs={'class': 'form-select'}),
            'streaming_movies': forms.Select(choices=SERVICE_ADDON_CHOICES, attrs={'class': 'form-select'}),
            'contract': forms.Select(choices=CONTRACT_CHOICES, attrs={'class': 'form-select'}),
            'paperless_billing': forms.Select(choices=YES_NO_CHOICES, attrs={'class': 'form-select'}),
            'payment_method': forms.Select(choices=PAYMENT_METHOD_CHOICES, attrs={'class': 'form-select'}),
            'monthly_charges': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_charges': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label='Select Customer Telemetry CSV',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'w-full rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 p-3 focus:ring-2 focus:ring-brand-500 outline-none'


class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 p-3 focus:ring-2 focus:ring-brand-500 outline-none',
            'placeholder': 'Username or Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 p-3 focus:ring-2 focus:ring-brand-500 outline-none',
            'placeholder': 'Password'
        })
    )
