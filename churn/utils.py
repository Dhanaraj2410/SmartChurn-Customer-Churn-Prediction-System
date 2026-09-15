import csv
import pandas as pd
import numpy as np
from io import BytesIO, StringIO
from django.http import HttpResponse

class RetentionEngine:
    @staticmethod
    def get_recommendations(customer_data, churn_probability, risk_level):
        recommendations = []
        contract = str(customer_data.get('Contract', customer_data.get('contract', ''))).lower()
        monthly = float(customer_data.get('MonthlyCharges', customer_data.get('monthly_charges', 0)) or 0)
        tenure = float(customer_data.get('tenure', 0) or 0)
        tech_support = str(customer_data.get('TechSupport', customer_data.get('tech_support', ''))).lower()
        payment_method = str(customer_data.get('PaymentMethod', customer_data.get('payment_method', ''))).lower()

        if risk_level == 'High':
            if 'month' in contract:
                recommendations.append({
                    'action': 'Offer 1-Year or 2-Year Contract Discount',
                    'reason': 'Customer is on a Month-to-Month contract with high churn risk. Switching to a long-term plan will reduce attrition.',
                    'priority': 'High Priority',
                    'icon': 'fas fa-file-contract'
                })
            if monthly > 70:
                recommendations.append({
                    'action': 'Custom Tariff Review & 15% Monthly Rebate',
                    'reason': 'High monthly fee (${:.2f}) is a primary churn contributor. Provide a temporary discount.'.format(monthly),
                    'priority': 'High Priority',
                    'icon': 'fas fa-percentage'
                })
            if tenure <= 6:
                recommendations.append({
                    'action': 'Proactive Onboarding Support Call',
                    'reason': 'New customer (tenure {:.0f} months) showing early churn signs. Contact within 24 hours.'.format(tenure),
                    'priority': 'Urgent',
                    'icon': 'fas fa-headset'
                })
            if 'no' in tech_support:
                recommendations.append({
                    'action': 'Complimentary 3-Month Tech Support Bundle',
                    'reason': 'Lack of tech support correlates with early exit. Offer free support add-on.',
                    'priority': 'Medium Priority',
                    'icon': 'fas fa-shield-alt'
                })
            if 'check' in payment_method:
                recommendations.append({
                    'action': 'Incentivize Automatic Payment Setup',
                    'reason': 'Manual check payments have lower retention. Offer $10 bill credit for Auto-pay enrollment.',
                    'priority': 'Medium Priority',
                    'icon': 'fas fa-credit-card'
                })
        elif risk_level == 'Medium':
            recommendations.append({
                'action': 'Send Targeted Satisfaction Survey & Feature Highlights',
                'reason': 'Customer shows moderate risk. Collect feedback before satisfaction drops further.',
                'priority': 'Medium Priority',
                'icon': 'fas fa-poll'
            })
            if 'month' in contract:
                recommendations.append({
                    'action': 'Promote Annual Subscription Bonus',
                    'reason': 'Encourage transition off month-to-month plan with gift voucher.',
                    'priority': 'Medium Priority',
                    'icon': 'fas fa-gift'
                })
        else: # Low Risk
            recommendations.append({
                'action': 'Premium Package Upsell Opportunity',
                'reason': 'Customer is highly satisfied with stable tenure. Prime candidate for streaming or bandwidth upgrade.',
                'priority': 'Low Priority',
                'icon': 'fas fa-rocket'
            })
            recommendations.append({
                'action': 'Invite to Customer Loyalty & Referral Program',
                'reason': 'High loyalty score. Leverage customer advocacy for referral rewards.',
                'priority': 'Low Priority',
                'icon': 'fas fa-heart'
            })

        return recommendations


class DataQualityAnalyzer:
    @staticmethod
    def analyze_dataframe(df):
        total_rows = len(df)
        total_cols = len(df.columns)

        if total_rows == 0:
            return {
                'total_rows': 0,
                'total_cols': total_cols,
                'missing_count': 0,
                'duplicate_count': 0,
                'invalid_count': 0,
                'quality_score': 0.0,
                'column_summary': {}
            }

        missing_count = int(df.isnull().sum().sum())
        duplicate_count = int(df.duplicated().sum())

        # Check for invalid values in numeric columns
        invalid_count = 0
        if 'TotalCharges' in df.columns:
            invalid_tc = pd.to_numeric(df['TotalCharges'], errors='coerce').isnull().sum()
            invalid_count += int(invalid_tc)
        if 'MonthlyCharges' in df.columns:
            invalid_mc = pd.to_numeric(df['MonthlyCharges'], errors='coerce').isnull().sum()
            invalid_count += int(invalid_mc)

        # Quality score formula
        max_flaws = (total_rows * total_cols) + total_rows
        actual_flaws = missing_count + (duplicate_count * total_cols) + invalid_count
        quality_score = max(0.0, round(100.0 * (1.0 - (actual_flaws / max(1, max_flaws))), 1))

        column_summary = {}
        for col in df.columns:
            col_missing = int(df[col].isnull().sum())
            column_summary[col] = {
                'dtype': str(df[col].dtype),
                'missing': col_missing,
                'unique': int(df[col].nunique())
            }

        return {
            'total_rows': total_rows,
            'total_cols': total_cols,
            'missing_count': missing_count,
            'duplicate_count': duplicate_count,
            'invalid_count': invalid_count,
            'quality_score': quality_score,
            'column_summary': column_summary
        }


def generate_csv_response(records, filename="predictions_export.csv"):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'Customer ID', 'Prediction', 'Probability (%)', 'Risk Level',
        'Confidence (%)', 'Date', 'Model Version'
    ])

    for rec in records:
        prob_pct = f"{rec.churn_probability * 100:.1f}" if hasattr(rec, 'churn_probability') else ""
        conf_pct = f"{rec.confidence * 100:.1f}" if hasattr(rec, 'confidence') else ""
        date_str = rec.prediction_date.strftime('%Y-%m-%d %H:%M') if hasattr(rec, 'prediction_date') else ""
        writer.writerow([
            rec.customer_id,
            rec.churn_prediction,
            prob_pct,
            rec.risk_level,
            conf_pct,
            date_str,
            rec.model_version
        ])

    return response


def generate_excel_response(records, filename="predictions_export.xlsx"):
    data = []
    for rec in records:
        data.append({
            'Customer ID': rec.customer_id,
            'Prediction': rec.churn_prediction,
            'Probability (%)': round(rec.churn_probability * 100, 1),
            'Risk Level': rec.risk_level,
            'Confidence (%)': round(rec.confidence * 100, 1),
            'Date': rec.prediction_date.strftime('%Y-%m-%d %H:%M') if hasattr(rec, 'prediction_date') else "",
            'Model Version': rec.model_version
        })

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Predictions')
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
