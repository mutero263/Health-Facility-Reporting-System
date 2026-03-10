"""
Health Facility Data Analyzer
Performs analysis on parsed health facility reports
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
from collections import defaultdict, Counter
from statistics import mean, median, stdev
import json

from health_parser import HealthReport, validate_report

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================
# CONSTANTS & THRESHOLDS
# ======================

# Alert thresholds (configurable)
ALERT_THRESHOLDS = {
    'malaria_positivity_rate': {
        'warning': 0.10,  # 10% positivity rate triggers warning
        'critical': 0.20,  # 20% positivity rate triggers critical alert
    },
    'opd_visits': {
        'zero_weeks': 2,  # 2 weeks of zero OPD visits triggers alert
        'sudden_drop': 0.5,  # 50% drop from average
    },
    'maternal_health': {
        'zero_deliveries_weeks': 4,  # 4 weeks with no deliveries
        'home_delivery_rate': 0.3,  # 30% home deliveries is concerning
    },
    'vaccination': {
        'zero_penta_weeks': 3,  # 3 weeks with no pentavalent vaccinations
    },
    'hiv_testing': {
        'zero_testing_weeks': 4,  # 4 weeks with no HIV tests
    },
    'tb_screening': {
        'low_screening': 10,  # Less than 10 TB screens per week
    },
    'data_quality': {
        'missing_rdns': True,
        'inconsistent_data': True,
    }
}

# Performance indicators
PERFORMANCE_INDICATORS = {
    'malaria_management': [
        'malaria_testing_rate',
        'malaria_positivity_rate',
        'malaria_treatment_rate'
    ],
    'maternal_health': [
        'anc_coverage',
        'institutional_delivery_rate',
        'pnc_coverage',
        'fp_acceptance_rate'
    ],
    'child_health': [
        'penta3_coverage',
        'vitamin_a_coverage',
        'sam_treatment_rate'
    ],
    'hiv_tb': [
        'hiv_testing_yield',
        'tb_screening_coverage',
        'tb_case_detection'
    ],
    'service_volume': [
        'opd_per_capita',
        'admission_rate',
        'major_surgery_rate'
    ]
}

# Target values (can be configured per district/facility)
DEFAULT_TARGETS = {
    'institutional_delivery_rate': 0.90,  # 90% of deliveries in facility
    'anc_coverage': 0.85,  # 85% of expected pregnancies
    'pnc_coverage': 0.80,  # 80% postnatal follow-up
    'penta3_coverage': 0.95,  # 95% vaccination coverage
    'malaria_testing_rate': 0.95,  # 95% of suspected cases tested
    'hiv_testing_yield': 0.05,  # 5% positivity rate expected
}


# ======================
# CORE ANALYSIS FUNCTIONS
# ======================

def analyze_weekly_data(reports: List[HealthReport]) -> Dict[str, Any]:
    """
    Analyze a list of weekly reports for a single facility
    """
    if not reports:
        return {}
    
    # Sort by week
    reports.sort(key=lambda x: (x.year, x.week))
    
    analysis = {
        'facility_name': reports[0].facility_name,
        'facility_id': reports[0].facility_id,
        'report_count': len(reports),
        'date_range': {
            'start': f"{reports[0].year}-W{reports[0].week}",
            'end': f"{reports[-1].year}-W{reports[-1].week}"
        },
        'summary': generate_facility_summary(reports),
        'trends': analyze_trends(reports),
        'performance_indicators': calculate_performance_indicators(reports),
        'alerts': generate_facility_alerts(reports),
        'comparison_to_targets': compare_to_targets(reports),
        'data_quality': assess_data_quality(reports),
        'anomalies': detect_anomalies(reports),
        'recommendations': generate_recommendations(reports)
    }
    
    return analysis


def generate_facility_summary(reports: List[HealthReport]) -> Dict[str, Any]:
    """Generate summary statistics for a facility"""
    summary = {}
    
    # Convert to DataFrame for easier aggregation
    df = reports_to_dataframe(reports)
    
    # Key metrics with totals
    summary['totals'] = {
        'opd_visits': int(df['opd_visits'].sum()),
        'institutional_deliveries': int(df['institutional_deliveries'].sum()),
        'home_deliveries': int(df['home_deliveries'].sum()),
        'anc_contacts': int(df['anc_contacts'].sum()),
        'fp_clients': int(df['fp_clients'].sum()),
        'pnc_attendees': int(df['pnc_attendees'].sum()),
        'hiv_tested': int(df['hiv_tested'].sum()),
        'children_vaccinated_penta3': int(df['children_vaccinated_penta3'].sum()),
        'tb_screened': int(df['tb_screened'].sum()),
        'malaria_tested': int(df['malaria_tested_numerator'].sum() if 'malaria_tested_numerator' in df.columns else 0),
        'malaria_positive': int(df['malaria_positive_numerator'].sum() if 'malaria_positive_numerator' in df.columns else 0),
    }
    
    # Averages
    summary['averages'] = {
        'avg_weekly_opd': float(df['opd_visits'].mean()),
        'avg_weekly_deliveries': float(df['institutional_deliveries'].mean()),
        'avg_weekly_anc': float(df['anc_contacts'].mean()),
        'avg_weekly_fp': float(df['fp_clients'].mean()),
        'avg_weekly_hiv_tests': float(df['hiv_tested'].mean()),
    }
    
    # Rates and ratios
    if summary['totals']['institutional_deliveries'] + summary['totals']['home_deliveries'] > 0:
        summary['rates'] = {
            'institutional_delivery_rate': round(
                summary['totals']['institutional_deliveries'] / 
                (summary['totals']['institutional_deliveries'] + summary['totals']['home_deliveries']), 3
            )
        }
    else:
        summary['rates'] = {'institutional_delivery_rate': 0}
    
    # Malaria positivity rate
    if summary['totals']['malaria_tested'] > 0:
        summary['rates']['malaria_positivity_rate'] = round(
            summary['totals']['malaria_positive'] / summary['totals']['malaria_tested'], 3
        )
    
    # ANC to delivery ratio (should be at least 4 per delivery)
    if summary['totals']['institutional_deliveries'] > 0:
        summary['ratios'] = {
            'anc_per_delivery': round(
                summary['totals']['anc_contacts'] / summary['totals']['institutional_deliveries'], 1
            )
        }
    
    return summary


def analyze_trends(reports: List[HealthReport]) -> Dict[str, Any]:
    """Analyze trends over time"""
    df = reports_to_dataframe(reports)
    
    # Ensure sorted by week/year
    df['period'] = df['year'].astype(str) + '-W' + df['week'].astype(str).str.zfill(2)
    
    trends = {}
    
    # Key metrics to track
    metrics = [
        'opd_visits', 'institutional_deliveries', 'anc_contacts', 
        'fp_clients', 'hiv_tested', 'children_vaccinated_penta3',
        'malaria_positive_numerator', 'malaria_tested_numerator'
    ]
    
    for metric in metrics:
        if metric in df.columns:
            values = df[metric].tolist()
            
            if len(values) >= 3:
                trends[metric] = {
                    'values': values,
                    'min': float(min(values)),
                    'max': float(max(values)),
                    'mean': float(mean(values)),
                    'median': float(median(values)),
                    'trend_direction': calculate_trend_direction(values),
                    'percentage_change': calculate_percentage_change(values),
                    'volatility': calculate_volatility(values)
                }
    
    # Seasonal patterns
    if len(df) >= 8:  # At least 8 weeks of data
        trends['seasonal_patterns'] = detect_seasonal_patterns(df)
    
    return trends


def calculate_trend_direction(values: List[float]) -> str:
    """Determine if trend is increasing, decreasing, or stable"""
    if len(values) < 3:
        return "insufficient_data"
    
    # Simple linear regression slope
    x = list(range(len(values)))
    y = values
    
    # Calculate slope
    n = len(x)
    slope = (n * sum(x[i] * y[i] for i in range(n)) - sum(x) * sum(y)) / \
            (n * sum(x[i] ** 2 for i in range(n)) - sum(x) ** 2) if n > 1 else 0
    
    if slope > 0.1:
        return "increasing"
    elif slope < -0.1:
        return "decreasing"
    else:
        return "stable"


def calculate_percentage_change(values: List[float]) -> float:
    """Calculate percentage change from first to last"""
    if len(values) < 2 or values[0] == 0:
        return 0
    
    return ((values[-1] - values[0]) / values[0]) * 100


def calculate_volatility(values: List[float]) -> float:
    """Calculate coefficient of variation as measure of volatility"""
    if len(values) < 2 or mean(values) == 0:
        return 0
    
    return stdev(values) / mean(values)


def detect_seasonal_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect seasonal patterns in the data"""
    patterns = {}
    
    # Add month information if not present
    if 'month' not in df.columns:
        # Approximate month from week number
        df['month'] = ((df['week'] - 1) // 4) + 1
    
    # Group by month
    monthly_avg = df.groupby('month').agg({
        'opd_visits': 'mean',
        'malaria_positive_numerator': 'mean' if 'malaria_positive_numerator' in df.columns else None,
        'institutional_deliveries': 'mean'
    }).to_dict()
    
    # Find peak months
    for metric, values in monthly_avg.items():
        if values and isinstance(values, dict):
            peak_month = max(values.items(), key=lambda x: x[1])[0]
            patterns[f'{metric}_peak_month'] = int(peak_month)
    
    return patterns


def calculate_performance_indicators(reports: List[HealthReport]) -> Dict[str, Any]:
    """Calculate key performance indicators"""
    df = reports_to_dataframe(reports)
    
    indicators = {}
    
    # Malaria testing rate
    if 'malaria_suspected_numerator' in df.columns and 'malaria_tested_numerator' in df.columns:
        total_suspected = df['malaria_suspected_numerator'].sum()
        total_tested = df['malaria_tested_numerator'].sum()
        
        if total_suspected > 0:
            indicators['malaria_testing_rate'] = round(total_tested / total_suspected, 3)
        else:
            indicators['malaria_testing_rate'] = 0
    
    # Malaria positivity rate
    if 'malaria_tested_numerator' in df.columns and 'malaria_positive_numerator' in df.columns:
        total_tested = df['malaria_tested_numerator'].sum()
        total_positive = df['malaria_positive_numerator'].sum()
        
        if total_tested > 0:
            indicators['malaria_positivity_rate'] = round(total_positive / total_tested, 3)
    
    # Institutional delivery rate
    total_deliveries = df['institutional_deliveries'].sum() + df['home_deliveries'].sum()
    if total_deliveries > 0:
        indicators['institutional_delivery_rate'] = round(
            df['institutional_deliveries'].sum() / total_deliveries, 3
        )
    
    # ANC coverage (approximation)
    # Assuming 4 ANC visits per pregnancy, and using deliveries as proxy for pregnancies
    total_deliveries = df['institutional_deliveries'].sum() + df['home_deliveries'].sum()
    expected_anc = total_deliveries * 4
    if expected_anc > 0:
        indicators['anc_coverage'] = round(
            min(df['anc_contacts'].sum() / expected_anc, 1.0), 3
        )
    
    # PNC coverage
    if total_deliveries > 0:
        indicators['pnc_coverage'] = round(
            df['pnc_attendees'].sum() / total_deliveries, 3
        )
    
    # HIV testing yield
    if 'hiv_tested' in df.columns and 'hiv_positive' in df.columns:
        total_tested = df['hiv_tested'].sum()
        total_positive = df['hiv_positive'].sum()
        
        if total_tested > 0:
            indicators['hiv_positivity_rate'] = round(total_positive / total_tested, 3)
    
    # TB screening coverage
    if 'tb_screened' in df.columns and 'opd_visits' in df.columns:
        total_opd = df['opd_visits'].sum()
        if total_opd > 0:
            indicators['tb_screening_rate'] = round(
                df['tb_screened'].sum() / total_opd, 3
            )
    
    return indicators


def generate_facility_alerts(reports: List[HealthReport]) -> List[Dict[str, Any]]:
    """Generate alerts based on the data"""
    alerts = []
    df = reports_to_dataframe(reports)
    
    # Check for zero values in critical metrics
    critical_metrics = [
        ('opd_visits', 'OPD visits'),
        ('institutional_deliveries', 'Institutional deliveries'),
        ('anc_contacts', 'ANC contacts'),
        ('children_vaccinated_penta3', 'Penta3 vaccinations')
    ]
    
    for metric, display_name in critical_metrics:
        if metric in df.columns:
            zero_weeks = (df[metric] == 0).sum()
            threshold = ALERT_THRESHOLDS.get(metric.split('_')[0], {}).get('zero_weeks', 2)
            
            if zero_weeks >= threshold:
                alerts.append({
                    'type': 'performance',
                    'severity': 'high' if zero_weeks >= threshold * 2 else 'medium',
                    'metric': metric,
                    'message': f"{display_name} reported as zero for {zero_weeks} weeks",
                    'weeks_affected': zero_weeks
                })
    
    # Malaria alerts
    if 'malaria_positivity_rate' in df.columns:
        avg_positivity = df['malaria_positivity_rate'].mean()
        
        if avg_positivity > ALERT_THRESHOLDS['malaria_positivity_rate']['critical']:
            alerts.append({
                'type': 'disease_surveillance',
                'severity': 'critical',
                'metric': 'malaria_positivity',
                'message': f"High malaria positivity rate: {avg_positivity:.1%}",
                'value': avg_positivity
            })
        elif avg_positivity > ALERT_THRESHOLDS['malaria_positivity_rate']['warning']:
            alerts.append({
                'type': 'disease_surveillance',
                'severity': 'warning',
                'metric': 'malaria_positivity',
                'message': f"Elevated malaria positivity rate: {avg_positivity:.1%}",
                'value': avg_positivity
            })
    
    # Sudden drop detection
    for metric in ['opd_visits', 'institutional_deliveries', 'anc_contacts']:
        if metric in df.columns and len(df) >= 4:
            recent_avg = df[metric].tail(2).mean()
            previous_avg = df[metric].head(len(df)-2).tail(2).mean()
            
            if previous_avg > 0 and recent_avg < previous_avg * 0.5:
                alerts.append({
                    'type': 'performance',
                    'severity': 'high',
                    'metric': metric,
                    'message': f"Sudden 50% drop in {metric} in last 2 weeks",
                    'recent_avg': float(recent_avg),
                    'previous_avg': float(previous_avg)
                })
    
    # Data quality alerts
    data_quality = assess_data_quality(reports)
    if data_quality['missing_data_weeks'] > 2:
        alerts.append({
            'type': 'data_quality',
            'severity': 'medium',
            'message': f"Missing data for {data_quality['missing_data_weeks']} weeks",
            'missing_weeks': data_quality['missing_weeks']
        })
    
    return alerts


def compare_to_targets(reports: List[HealthReport]) -> Dict[str, Any]:
    """Compare facility performance to targets"""
    indicators = calculate_performance_indicators(reports)
    
    comparison = {}
    
    for indicator, value in indicators.items():
        if indicator in DEFAULT_TARGETS:
            target = DEFAULT_TARGETS[indicator]
            comparison[indicator] = {
                'actual': value,
                'target': target,
                'achieved': value >= target,
                'gap': round(max(0, target - value), 3),
                'percentage_of_target': round((value / target) * 100 if target > 0 else 0, 1)
            }
    
    return comparison


def assess_data_quality(reports: List[HealthReport]) -> Dict[str, Any]:
    """Assess the quality of the data"""
    quality = {
        'total_reports': len(reports),
        'complete_reports': 0,
        'missing_data_weeks': 0,
        'missing_weeks': [],
        'inconsistent_data': [],
        'quality_score': 0
    }
    
    # Check for missing weeks
    if reports:
        weeks = [(r.year, r.week) for r in reports]
        weeks.sort()
        
        expected_weeks = []
        if weeks:
            start_year, start_week = weeks[0]
            end_year, end_week = weeks[-1]
            
            # Generate expected weeks (simplified)
            current_year, current_week = start_year, start_week
            while (current_year, current_week) <= (end_year, end_week):
                expected_weeks.append((current_year, current_week))
                current_week += 1
                if current_week > 52:
                    current_week = 1
                    current_year += 1
        
        missing = set(expected_weeks) - set(weeks)
        quality['missing_data_weeks'] = len(missing)
        quality['missing_weeks'] = [f"{y}-W{w}" for y, w in missing]
    
    # Check each report for completeness
    for report in reports:
        warnings = validate_report(report)
        if not warnings:
            quality['complete_reports'] += 1
        else:
            quality['inconsistent_data'].extend(warnings)
    
    # Calculate quality score (0-100)
    if reports:
        completeness_score = (quality['complete_reports'] / len(reports)) * 50
        missing_score = max(0, 50 - (quality['missing_data_weeks'] * 5))
        quality['quality_score'] = min(100, completeness_score + missing_score)
    
    return quality


def detect_anomalies(reports: List[HealthReport]) -> List[Dict[str, Any]]:
    """Detect anomalies in the data"""
    anomalies = []
    df = reports_to_dataframe(reports)
    
    # Z-score based anomaly detection for key metrics
    metrics = ['opd_visits', 'institutional_deliveries', 'anc_contacts']
    
    for metric in metrics:
        if metric in df.columns and len(df) >= 5:
            mean_val = df[metric].mean()
            std_val = df[metric].std()
            
            if std_val > 0:
                for idx, row in df.iterrows():
                    z_score = abs(row[metric] - mean_val) / std_val
                    
                    if z_score > 3:  # More than 3 standard deviations
                        anomalies.append({
                            'type': 'statistical_outlier',
                            'metric': metric,
                            'week': f"{row['year']}-W{row['week']}",
                            'value': float(row[metric]),
                            'expected_range': {
                                'mean': float(mean_val),
                                'std': float(std_val),
                                'lower': float(mean_val - 2*std_val),
                                'upper': float(mean_val + 2*std_val)
                            },
                            'z_score': float(z_score)
                        })
    
    return anomalies


def generate_recommendations(reports: List[HealthReport]) -> List[Dict[str, Any]]:
    """Generate actionable recommendations based on the data"""
    recommendations = []
    df = reports_to_dataframe(reports)
    indicators = calculate_performance_indicators(reports)
    comparison = compare_to_targets(reports)
    
    # Malaria testing recommendations
    if 'malaria_testing_rate' in indicators:
        if indicators['malaria_testing_rate'] < 0.8:
            recommendations.append({
                'area': 'malaria',
                'priority': 'high',
                'message': "Malaria testing rate is below 80%. Ensure all suspected cases are tested.",
                'current_rate': indicators['malaria_testing_rate']
            })
    
    # Institutional delivery recommendations
    if 'institutional_delivery_rate' in indicators:
        if indicators['institutional_delivery_rate'] < DEFAULT_TARGETS['institutional_delivery_rate']:
            recommendations.append({
                'area': 'maternal_health',
                'priority': 'high',
                'message': f"Institutional delivery rate is {indicators['institutional_delivery_rate']:.1%}. Target is {DEFAULT_TARGETS['institutional_delivery_rate']:.0%}. Strengthen referral system and community awareness.",
                'current_rate': indicators['institutional_delivery_rate']
            })
    
    # ANC coverage recommendations
    if 'anc_coverage' in indicators:
        if indicators['anc_coverage'] < DEFAULT_TARGETS['anc_coverage']:
            recommendations.append({
                'area': 'maternal_health',
                'priority': 'medium',
                'message': f"ANC coverage is {indicators['anc_coverage']:.1%}. Target is {DEFAULT_TARGETS['anc_coverage']:.0%}. Increase outreach and early pregnancy identification.",
                'current_rate': indicators['anc_coverage']
            })
    
    # PNC coverage recommendations
    if 'pnc_coverage' in indicators:
        if indicators['pnc_coverage'] < DEFAULT_TARGETS['pnc_coverage']:
            recommendations.append({
                'area': 'maternal_health',
                'priority': 'medium',
                'message': f"PNC coverage is {indicators['pnc_coverage']:.1%}. Target is {DEFAULT_TARGETS['pnc_coverage']:.0%}. Strengthen follow-up of postnatal mothers.",
                'current_rate': indicators['pnc_coverage']
            })
    
    # Data quality recommendations
    data_quality = assess_data_quality(reports)
    if data_quality['missing_data_weeks'] > 0:
        recommendations.append({
            'area': 'data_quality',
            'priority': 'medium',
            'message': f"Missing data for {data_quality['missing_data_weeks']} weeks. Ensure timely weekly reporting.",
            'missing_weeks': data_quality['missing_data_weeks']
        })
    
    # Zero value recommendations
    zero_counts = {}
    for metric in ['opd_visits', 'institutional_deliveries', 'anc_contacts']:
        if metric in df.columns:
            zero_weeks = (df[metric] == 0).sum()
            if zero_weeks > 2:
                zero_counts[metric] = zero_weeks
    
    if zero_counts:
        recommendations.append({
            'area': 'data_verification',
            'priority': 'high',
            'message': "Multiple weeks with zero values detected. Please verify if this is accurate.",
            'zero_metrics': zero_counts
        })
    
    return recommendations


# ======================
# FACILITY COMPARISON FUNCTIONS
# ======================

def compare_facilities(facility_reports: Dict[int, List[HealthReport]], 
                       metrics: List[str] = None) -> Dict[str, Any]:
    """
    Compare multiple facilities
    
    Args:
        facility_reports: Dictionary mapping facility_id to list of reports
        metrics: List of metrics to compare (default: all key metrics)
    
    Returns:
        Comparison dictionary
    """
    if not metrics:
        metrics = [
            'opd_visits', 'institutional_deliveries', 'anc_contacts',
            'fp_clients', 'hiv_tested', 'children_vaccinated_penta3'
        ]
    
    comparison = {
        'facility_count': len(facility_reports),
        'period': {},
        'rankings': {},
        'averages': {},
        'best_performers': {},
        'needs_improvement': {}
    }
    
    # Get date range across all facilities
    all_dates = []
    for reports in facility_reports.values():
        if reports:
            all_dates.append((reports[0].year, reports[0].week))
            all_dates.append((reports[-1].year, reports[-1].week))
    
    if all_dates:
        comparison['period'] = {
            'start': f"{min(all_dates)[0]}-W{min(all_dates)[1]}",
            'end': f"{max(all_dates)[0]}-W{max(all_dates)[1]}"
        }
    
    # Calculate summary statistics for each facility
    facility_summaries = {}
    for facility_id, reports in facility_reports.items():
        if reports:
            summary = generate_facility_summary(reports)
            facility_summaries[facility_id] = {
                'name': reports[0].facility_name,
                'summary': summary
            }
    
    # Calculate rankings for each metric
    for metric in metrics:
        metric_values = {}
        for facility_id, data in facility_summaries.items():
            # Try to get from totals
            if 'totals' in data['summary'] and metric in data['summary']['totals']:
                value = data['summary']['totals'][metric]
                metric_values[facility_id] = {
                    'name': data['name'],
                    'value': value
                }
        
        if metric_values:
            # Sort by value descending
            sorted_values = sorted(metric_values.items(), 
                                   key=lambda x: x[1]['value'], 
                                   reverse=True)
            
            comparison['rankings'][metric] = [
                {
                    'facility_id': fid,
                    'facility_name': val['name'],
                    'value': val['value'],
                    'rank': idx + 1
                }
                for idx, (fid, val) in enumerate(sorted_values)
            ]
            
            # Best performer
            if sorted_values:
                comparison['best_performers'][metric] = {
                    'facility_id': sorted_values[0][0],
                    'facility_name': sorted_values[0][1]['name'],
                    'value': sorted_values[0][1]['value']
                }
            
            # Needs improvement (worst performer with non-zero)
            non_zero = [(fid, val) for fid, val in metric_values.items() if val['value'] > 0]
            if non_zero:
                worst = sorted(non_zero, key=lambda x: x[1]['value'])[0]
                comparison['needs_improvement'][metric] = {
                    'facility_id': worst[0],
                    'facility_name': worst[1]['name'],
                    'value': worst[1]['value']
                }
    
    # Calculate district-wide averages
    for metric in metrics:
        values = []
        for data in facility_summaries.values():
            if 'totals' in data['summary'] and metric in data['summary']['totals']:
                values.append(data['summary']['totals'][metric])
        
        if values:
            comparison['averages'][metric] = {
                'mean': mean(values),
                'median': median(values),
                'total': sum(values),
                'min': min(values),
                'max': max(values)
            }
    
    return comparison


def calculate_facility_stats(reports: List[HealthReport]) -> Dict[str, Any]:
    """Calculate comprehensive statistics for a facility"""
    stats = {}
    
    df = reports_to_dataframe(reports)
    
    # Basic stats
    stats['report_count'] = len(reports)
    
    # Weekly statistics for key metrics
    key_metrics = [
        'opd_visits', 'institutional_deliveries', 'anc_contacts',
        'fp_clients', 'pnc_attendees', 'hiv_tested',
        'children_vaccinated_penta3', 'tb_screened'
    ]
    
    for metric in key_metrics:
        if metric in df.columns:
            stats[metric] = {
                'total': int(df[metric].sum()),
                'weekly_avg': float(df[metric].mean()),
                'weekly_median': float(df[metric].median()),
                'min_week': int(df[metric].min()),
                'max_week': int(df[metric].max()),
                'zero_weeks': int((df[metric] == 0).sum())
            }
    
    # Malaria statistics
    if 'malaria_tested_numerator' in df.columns:
        stats['malaria'] = {
            'total_tested': int(df['malaria_tested_numerator'].sum()),
            'total_positive': int(df['malaria_positive_numerator'].sum()),
            'avg_positivity_rate': float(
                df['malaria_positive_numerator'].sum() / df['malaria_tested_numerator'].sum() 
                if df['malaria_tested_numerator'].sum() > 0 else 0
            )
        }
    
    # Ratios
    if stats.get('institutional_deliveries', {}).get('total', 0) > 0:
        stats['ratios'] = {
            'anc_per_delivery': round(
                stats['anc_contacts']['total'] / stats['institutional_deliveries']['total'], 1
            ),
            'pnc_per_delivery': round(
                stats['pnc_attendees']['total'] / stats['institutional_deliveries']['total'], 1
            )
        }
    
    return stats


# ======================
# DISTRICT/PROVINCE LEVEL ANALYSIS
# ======================

def analyze_district(facilities_data: Dict[int, List[HealthReport]], 
                     district_name: str) -> Dict[str, Any]:
    """
    Analyze all facilities in a district
    
    Args:
        facilities_data: Dictionary mapping facility_id to list of reports
        district_name: Name of the district
    
    Returns:
        District-level analysis
    """
    analysis = {
        'district_name': district_name,
        'facility_count': len(facilities_data),
        'reporting_rate': calculate_reporting_rate(facilities_data),
        'summary': generate_district_summary(facilities_data),
        'facility_performance': rank_facilities(facilities_data),
        'top_performers': [],
        'underperformers': [],
        'alerts': [],
        'recommendations': []
    }
    
    # Generate district-wide alerts
    for facility_id, reports in facilities_data.items():
        facility_alerts = generate_facility_alerts(reports)
        if facility_alerts:
            facility_name = reports[0].facility_name if reports else f"Facility {facility_id}"
            analysis['alerts'].extend([
                {**alert, 'facility_id': facility_id, 'facility_name': facility_name}
                for alert in facility_alerts
            ])
    
    # Identify top and under performers
    for metric in ['institutional_delivery_rate', 'anc_coverage', 'penta3_coverage']:
        best = find_best_performer(facilities_data, metric)
        if best:
            analysis['top_performers'].append(best)
        
        worst = find_worst_performer(facilities_data, metric)
        if worst and worst['value'] > 0:  # Only include if they have any activity
            analysis['underperformers'].append(worst)
    
    # District recommendations
    if analysis['reporting_rate'] < 80:
        analysis['recommendations'].append({
            'priority': 'high',
            'message': f"Reporting rate is only {analysis['reporting_rate']:.0f}%. Improve timely reporting from all facilities."
        })
    
    # Check for disease outbreaks
    outbreak_risk = assess_outbreak_risk(facilities_data)
    if outbreak_risk:
        analysis['recommendations'].extend(outbreak_risk)
    
    return analysis


def calculate_reporting_rate(facilities_data: Dict[int, List[HealthReport]]) -> float:
    """Calculate percentage of facilities reporting"""
    reporting_facilities = sum(1 for reports in facilities_data.values() if reports)
    total_facilities = len(facilities_data)
    
    return (reporting_facilities / total_facilities) * 100 if total_facilities > 0 else 0


def generate_district_summary(facilities_data: Dict[int, List[HealthReport]]) -> Dict[str, Any]:
    """Generate district-wide summary"""
    summary = {
        'totals': defaultdict(int),
        'averages': {}
    }
    
    # Aggregate all reports
    all_reports = []
    for reports in facilities_data.values():
        all_reports.extend(reports)
    
    if all_reports:
        df = reports_to_dataframe(all_reports)
        
        # Calculate totals
        for metric in ['opd_visits', 'institutional_deliveries', 'anc_contacts', 
                       'fp_clients', 'hiv_tested', 'children_vaccinated_penta3']:
            if metric in df.columns:
                summary['totals'][metric] = int(df[metric].sum())
        
        # Calculate averages
        for metric, total in summary['totals'].items():
            summary['averages'][metric] = round(total / len(facilities_data), 1)
    
    return dict(summary)


def rank_facilities(facilities_data: Dict[int, List[HealthReport]]) -> Dict[str, List]:
    """Rank facilities by various metrics"""
    rankings = {}
    
    # Composite score based on multiple indicators
    facility_scores = []
    
    for facility_id, reports in facilities_data.items():
        if not reports:
            continue
            
        indicators = calculate_performance_indicators(reports)
        facility_name = reports[0].facility_name
        
        # Calculate composite score (0-100)
        score = 0
        components = []
        
        # Institutional delivery rate (30 points)
        if 'institutional_delivery_rate' in indicators:
            idr_score = indicators['institutional_delivery_rate'] * 30
            score += idr_score
            components.append(('idr', idr_score))
        
        # ANC coverage (25 points)
        if 'anc_coverage' in indicators:
            anc_score = indicators['anc_coverage'] * 25
            score += anc_score
            components.append(('anc', anc_score))
        
        # Penta3 coverage (25 points)
        # Approximate from children_vaccinated_penta3 vs expected
        # This is simplified - in reality would use target population
        
        # Data quality (20 points)
        quality = assess_data_quality(reports)
        score += quality['quality_score'] * 0.2
        
        facility_scores.append({
            'facility_id': facility_id,
            'facility_name': facility_name,
            'score': round(score, 1),
            'components': components
        })
    
    # Sort by score
    facility_scores.sort(key=lambda x: x['score'], reverse=True)
    
    rankings['overall'] = facility_scores
    
    return rankings


def find_best_performer(facilities_data: Dict[int, List[HealthReport]], 
                        metric: str) -> Optional[Dict]:
    """Find the best performing facility for a given metric"""
    best = None
    best_value = -1
    
    for facility_id, reports in facilities_data.items():
        if not reports:
            continue
            
        indicators = calculate_performance_indicators(reports)
        
        if metric in indicators and indicators[metric] > best_value:
            best_value = indicators[metric]
            best = {
                'facility_id': facility_id,
                'facility_name': reports[0].facility_name,
                'metric': metric,
                'value': best_value
            }
    
    return best


def find_worst_performer(facilities_data: Dict[int, List[HealthReport]], 
                         metric: str) -> Optional[Dict]:
    """Find the worst performing facility for a given metric"""
    worst = None
    worst_value = float('inf')
    
    for facility_id, reports in facilities_data.items():
        if not reports:
            continue
            
        indicators = calculate_performance_indicators(reports)
        
        if metric in indicators and 0 <= indicators[metric] < worst_value:
            worst_value = indicators[metric]
            worst = {
                'facility_id': facility_id,
                'facility_name': reports[0].facility_name,
                'metric': metric,
                'value': worst_value
            }
    
    return worst


def assess_outbreak_risk(facilities_data: Dict[int, List[HealthReport]]) -> List[Dict]:
    """Assess risk of disease outbreaks across the district"""
    recommendations = []
    
    # Aggregate malaria data
    all_malaria_rates = []
    facilities_with_spike = []
    
    for facility_id, reports in facilities_data.items():
        if not reports:
            continue
            
        df = reports_to_dataframe(reports)
        
        if 'malaria_positivity_rate' in df.columns:
            recent_rate = df['malaria_positivity_rate'].tail(2).mean()
            previous_rate = df['malaria_positivity_rate'].head(len(df)-2).tail(2).mean() if len(df) > 4 else 0
            
            if recent_rate > 0.15 and recent_rate > previous_rate * 1.5:
                facilities_with_spike.append({
                    'facility_id': facility_id,
                    'facility_name': reports[0].facility_name,
                    'recent_rate': float(recent_rate),
                    'previous_rate': float(previous_rate)
                })
            
            all_malaria_rates.append(recent_rate)
    
    # District-wide assessment
    if facilities_with_spike:
        recommendations.append({
            'priority': 'high',
            'type': 'outbreak',
            'message': f"Malaria spike detected in {len(facilities_with_spike)} facilities. Investigate and implement vector control.",
            'facilities_affected': facilities_with_spike
        })
    
    # Check for diarrhoea outbreaks
    # This would use diarrhoea data - simplified for now
    
    return recommendations


# ======================
# ALERTS GENERATION (NEW FUNCTION)
# ======================

def generate_alerts(conn, report):
    """
    Generate alerts based on report data
    
    Args:
        conn: Database connection
        report: HealthReport object
        
    Returns:
        List of alert dictionaries
    """
    alerts = []
    
    # Check for critical values in malaria data
    if hasattr(report, 'malaria_positive') and hasattr(report, 'malaria_tested'):
        pos_num, pos_den = report.get_fraction_parts('malaria_positive')
        tested_num, tested_den = report.get_fraction_parts('malaria_tested')
        
        if tested_num > 0:
            positivity_rate = pos_num / tested_num
            if positivity_rate > 0.2:  # 20% threshold
                alerts.append({
                    'facility_id': report.facility_id,
                    'week': report.week,
                    'year': report.year,
                    'alert_type': 'disease_surveillance',
                    'severity': 'critical',
                    'message': f'High malaria positivity rate: {positivity_rate:.1%}'
                })
            elif positivity_rate > 0.1:  # 10% threshold
                alerts.append({
                    'facility_id': report.facility_id,
                    'week': report.week,
                    'year': report.year,
                    'alert_type': 'disease_surveillance',
                    'severity': 'high',
                    'message': f'Elevated malaria positivity rate: {positivity_rate:.1%}'
                })
    
    # Check for zero OPD visits
    if hasattr(report, 'opd_visits') and report.opd_visits == 0:
        alerts.append({
            'facility_id': report.facility_id,
            'week': report.week,
            'year': report.year,
            'alert_type': 'data_quality',
            'severity': 'warning',
            'message': 'OPD visits reported as zero - please verify'
        })
    
    # Check for zero deliveries with ANC contacts
    if hasattr(report, 'institutional_deliveries') and hasattr(report, 'anc_contacts'):
        if report.institutional_deliveries == 0 and report.anc_contacts > 0:
            alerts.append({
                'facility_id': report.facility_id,
                'week': report.week,
                'year': report.year,
                'alert_type': 'data_quality',
                'severity': 'warning',
                'message': 'ANC contacts reported but no deliveries - please verify'
            })
    
    # Check for high home delivery rate
    if hasattr(report, 'home_deliveries') and hasattr(report, 'institutional_deliveries'):
        total_deliveries = report.home_deliveries + report.institutional_deliveries
        if total_deliveries > 0:
            home_delivery_rate = report.home_deliveries / total_deliveries
            if home_delivery_rate > 0.3:  # 30% threshold
                alerts.append({
                    'facility_id': report.facility_id,
                    'week': report.week,
                    'year': report.year,
                    'alert_type': 'performance',
                    'severity': 'high',
                    'message': f'High home delivery rate: {home_delivery_rate:.1%}'
                })
    
    # Check for missing HIV testing
    if hasattr(report, 'hiv_tested') and report.hiv_tested == 0 and hasattr(report, 'opd_visits') and report.opd_visits > 50:
        alerts.append({
            'facility_id': report.facility_id,
            'week': report.week,
            'year': report.year,
            'alert_type': 'performance',
            'severity': 'medium',
            'message': 'No HIV tests reported despite high OPD volume'
        })
    
    # Check for zero vaccinations
    if hasattr(report, 'children_vaccinated_penta3') and report.children_vaccinated_penta3 == 0:
        alerts.append({
            'facility_id': report.facility_id,
            'week': report.week,
            'year': report.year,
            'alert_type': 'performance',
            'severity': 'medium',
            'message': 'No Penta3 vaccinations reported - please verify'
        })
    
    return alerts


# ======================
# UTILITY FUNCTIONS
# ======================

def reports_to_dataframe(reports: List[HealthReport]) -> pd.DataFrame:
    """Convert list of HealthReport objects to pandas DataFrame"""
    if not reports:
        return pd.DataFrame()
    
    # Convert each report to dict
    data = []
    for report in reports:
        row = {
            'facility_id': report.facility_id,
            'facility_name': report.facility_name,
            'week': report.week,
            'year': report.year,
            'opd_visits': report.opd_visits,
            'institutional_deliveries': report.institutional_deliveries,
            'home_deliveries': report.home_deliveries,
            'anc_contacts': report.anc_contacts,
            'fp_clients': report.fp_clients,
            'pnc_attendees': report.pnc_attendees,
            'hiv_tested': report.hiv_tested,
            'children_vaccinated_penta3': report.children_vaccinated_penta3,
            'tb_screened': report.tb_screened,
            'under5_sam': report.under5_sam,
            'under5_mam': report.under5_mam,
            'institutional_deaths': report.institutional_deaths,
            'functional_ambulance': report.functional_ambulance,
        }
        
        # Add fraction components
        num, den = report.get_fraction_parts('malaria_suspected')
        row['malaria_suspected_numerator'] = num
        row['malaria_suspected_denominator'] = den
        if den > 0:
            row['malaria_suspected_rate'] = num / den
        
        num, den = report.get_fraction_parts('malaria_tested')
        row['malaria_tested_numerator'] = num
        row['malaria_tested_denominator'] = den
        if den > 0:
            row['malaria_tested_rate'] = num / den
        
        num, den = report.get_fraction_parts('malaria_positive')
        row['malaria_positive_numerator'] = num
        row['malaria_positive_denominator'] = den
        if den > 0:
            row['malaria_positive_rate'] = num / den
        
        # Malaria positivity rate (tested vs positive)
        if row['malaria_tested_numerator'] > 0:
            row['malaria_positivity_rate'] = row['malaria_positive_numerator'] / row['malaria_tested_numerator']
        else:
            row['malaria_positivity_rate'] = 0
        
        data.append(row)
    
    return pd.DataFrame(data)


def get_facility_trends(reports: List[HealthReport]) -> Dict[str, Any]:
    """Get trend data for a facility (for API/charting)"""
    df = reports_to_dataframe(reports)
    
    if df.empty:
        return {}
    
    # Sort by week/year
    df = df.sort_values(['year', 'week'])
    
    # Create period labels
    df['period'] = df['year'].astype(str) + '-W' + df['week'].astype(str).str.zfill(2)
    
    trends = {
        'labels': df['period'].tolist(),
        'datasets': {}
    }
    
    # Add key metrics
    metrics = [
        'opd_visits', 'institutional_deliveries', 'anc_contacts',
        'fp_clients', 'hiv_tested', 'children_vaccinated_penta3',
        'malaria_positivity_rate'
    ]
    
    for metric in metrics:
        if metric in df.columns:
            trends['datasets'][metric] = df[metric].tolist()
    
    return trends


def export_analysis_json(analysis: Dict[str, Any], filepath: str):
    """Export analysis to JSON file"""
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            return super().default(obj)
    
    with open(filepath, 'w') as f:
        json.dump(analysis, f, indent=2, cls=DateTimeEncoder)


# ======================
# MAIN TEST FUNCTION
# ======================

if __name__ == "__main__":
    # Test with sample data
    from health_parser import parse_health_report
    
    sample_reports = []
    
    # Create a few sample reports (would come from database in real usage)
    sample_text1 = """
    Matotwe rhc
    Week 9
    Malaria suspected 5/10
    Tested 8/10
    Positive 2/8
    OPD visits 45
    Institutional deliveries 3
    ANC contacts 5
    """
    
    report1 = parse_health_report(sample_text1)
    report1.facility_id = 1
    sample_reports.append(report1)
    
    sample_text2 = """
    Matotwe rhc
    Week 10
    Malaria suspected 6/12
    Tested 10/12
    Positive 3/10
    OPD visits 52
    Institutional deliveries 4
    ANC contacts 6
    """
    
    report2 = parse_health_report(sample_text2)
    report2.facility_id = 1
    sample_reports.append(report2)
    
    # Analyze facility
    analysis = analyze_weekly_data(sample_reports)
    
    print("Facility Analysis Results:")
    print(json.dumps(analysis, indent=2, default=str))
    
    # Test facility comparison
    facility_reports = {
        1: sample_reports,
        2: [report1]  # Another facility with just one report
    }
    
    comparison = compare_facilities(facility_reports)
    print("\nFacility Comparison:")
    print(json.dumps(comparison, indent=2, default=str))