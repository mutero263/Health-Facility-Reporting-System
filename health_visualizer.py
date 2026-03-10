"""
Health Facility Data Visualizer
Creates charts, graphs, and dashboards for health facility data
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime
import io
import base64
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json

from health_parser import HealthReport
from health_analyzer import reports_to_dataframe, calculate_performance_indicators

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================
# CONFIGURATION
# ======================

# Color schemes
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'success': '#28A745',
    'warning': '#FFC107',
    'danger': '#DC3545',
    'info': '#17A2B8',
    'light': '#F8F9FA',
    'dark': '#343A40',
    
    # Metric-specific
    'opd': '#2E86AB',
    'malaria': '#DC3545',
    'maternal': '#A23B72',
    'child': '#28A745',
    'hiv': '#FFC107',
    'tb': '#17A2B8',
    
    # Gradients
    'gradient_blue': ['#c6e2ff', '#2E86AB', '#1a4b6d'],
    'gradient_green': ['#d4edda', '#28A745', '#155724'],
    'gradient_red': ['#f8d7da', '#DC3545', '#721c24'],
}

# Chart styling
CHART_STYLE = {
    'figure.figsize': (12, 6),
    'figure.dpi': 100,
    'font.size': 10,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 16,
}

plt.style.use('seaborn-v0_8-darkgrid')
matplotlib.rcParams.update(CHART_STYLE)

# ======================
# FACILITY DASHBOARD
# ======================

def generate_facility_dashboard(facility_name: str, 
                                reports: List[HealthReport],
                                output_dir: Path,
                                include_plotly: bool = True) -> Dict[str, Path]:
    """
    Generate a comprehensive dashboard for a single facility
    
    Returns:
        Dictionary mapping chart names to file paths
    """
    logger.info(f"Generating dashboard for {facility_name}")
    
    # Create facility-specific subdirectory
    facility_dir = output_dir / facility_name.replace(' ', '_').lower()
    facility_dir.mkdir(exist_ok=True, parents=True)
    
    # Convert to DataFrame
    df = reports_to_dataframe(reports)
    
    if df.empty:
        logger.warning(f"No data for {facility_name}")
        return {}
    
    # Sort by date
    df = df.sort_values(['year', 'week'])
    df['period'] = df['year'].astype(str) + '-W' + df['week'].astype(str).str.zfill(2)
    
    # Generate individual charts
    charts = {}
    
    # 1. Key metrics overview (summary cards - saved as PNG but also returned as data)
    charts['summary_cards'] = create_summary_cards(df, facility_dir)
    
    # 2. OPD trends
    charts['opd_trends'] = create_opd_trends(df, facility_dir)
    
    # 3. Malaria surveillance
    charts['malaria_chart'] = create_malaria_chart(df, facility_dir)
    
    # 4. Maternal health
    charts['maternal_health'] = create_maternal_health_chart(df, facility_dir)
    
    # 5. Child health
    charts['child_health'] = create_child_health_chart(df, facility_dir)
    
    # 6. HIV/TB services
    charts['hiv_tb'] = create_hiv_tb_chart(df, facility_dir)
    
    # 7. Performance radar
    charts['performance_radar'] = create_performance_radar(df, facility_dir)
    
    # 8. Data quality heatmap
    charts['data_quality'] = create_data_quality_heatmap(df, facility_dir)
    
    # 9. Weekly comparison (last 4 weeks vs average)
    charts['weekly_comparison'] = create_weekly_comparison(df, facility_dir)
    
    # 10. Distribution histograms
    charts['distributions'] = create_distribution_plots(df, facility_dir)
    
    # Create combined dashboard (multi-panel figure)
    charts['combined_dashboard'] = create_combined_dashboard(df, facility_name, facility_dir)
    
    # Create interactive Plotly dashboard if requested
    if include_plotly:
        charts['interactive_dashboard'] = create_plotly_dashboard(df, facility_name, facility_dir)
    
    logger.info(f"Generated {len(charts)} charts for {facility_name}")
    
    return charts


def create_summary_cards(df: pd.DataFrame, output_dir: Path) -> Path:
    """Create summary statistics cards"""
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.axis('off')
    
    # Calculate key metrics
    total_opd = int(df['opd_visits'].sum())
    avg_weekly_opd = int(df['opd_visits'].mean())
    
    total_deliveries = int(df['institutional_deliveries'].sum())
    total_anc = int(df['anc_contacts'].sum())
    
    total_hiv_tested = int(df['hiv_tested'].sum())
    total_vaccinated = int(df['children_vaccinated_penta3'].sum())
    
    # Create cards as text boxes
    cards = [
        {'title': 'Total OPD Visits', 'value': f'{total_opd:,}', 'color': COLORS['opd']},
        {'title': 'Avg Weekly OPD', 'value': f'{avg_weekly_opd:,}', 'color': COLORS['opd']},
        {'title': 'Deliveries', 'value': f'{total_deliveries}', 'color': COLORS['maternal']},
        {'title': 'ANC Contacts', 'value': f'{total_anc}', 'color': COLORS['maternal']},
        {'title': 'HIV Tests', 'value': f'{total_hiv_tested}', 'color': COLORS['hiv']},
        {'title': 'Penta3 Vaccinations', 'value': f'{total_vaccinated}', 'color': COLORS['child']},
    ]
    
    # Position cards
    for i, card in enumerate(cards):
        x = 0.15 + (i * 0.16)
        y = 0.5
        
        # Card background
        rect = plt.Rectangle((x-0.12, y-0.3), 0.14, 0.4, 
                             facecolor=card['color'], alpha=0.1,
                             edgecolor=card['color'], linewidth=2,
                             transform=fig.transFigure)
        fig.patches.append(rect)
        
        # Title
        ax.text(x, y, card['title'], 
                ha='center', va='center', fontsize=10, fontweight='bold',
                transform=fig.transFigure)
        
        # Value
        ax.text(x, y-0.15, card['value'], 
                ha='center', va='center', fontsize=16, fontweight='bold',
                color=card['color'], transform=fig.transFigure)
    
    plt.tight_layout()
    
    output_path = output_dir / 'summary_cards.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path


def create_opd_trends(df: pd.DataFrame, output_dir: Path) -> Path:
    """Create OPD trends chart"""
    fig, ax = plt.subplots(figsize=(12, 5))
    
    periods = df['period'].tolist()
    opd_values = df['opd_visits'].tolist()
    
    # Line chart with markers
    ax.plot(periods, opd_values, marker='o', linestyle='-', 
            linewidth=2, markersize=6, color=COLORS['opd'], 
            markerfacecolor='white', markeredgewidth=2, markeredgecolor=COLORS['opd'])
    
    # Add trend line
    if len(opd_values) > 1:
        z = np.polyfit(range(len(opd_values)), opd_values, 1)
        p = np.poly1d(z)
        ax.plot(periods, p(range(len(opd_values))), 
                linestyle='--', color='gray', alpha=0.7, linewidth=1.5,
                label=f'Trend (slope: {z[0]:.1f})')
    
    # Calculate moving average
    if len(opd_values) >= 4:
        ma = pd.Series(opd_values).rolling(window=4, min_periods=1).mean()
        ax.plot(periods, ma, linestyle=':', color='darkblue', alpha=0.7,
                label='4-week moving average')
    
    # Formatting
    ax.set_title('OPD Visits Over Time', fontsize=14, fontweight='bold')
    ax.set_xlabel('Week')
    ax.set_ylabel('Number of Visits')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best')
    
    # Rotate x labels if too many
    if len(periods) > 10:
        plt.xticks(rotation=45, ha='right')
    
    # Add annotations for key points
    max_idx = opd_values.index(max(opd_values))
    ax.annotate(f'Peak: {opd_values[max_idx]}', 
                xy=(periods[max_idx], opd_values[max_idx]),
                xytext=(10, 10), textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    plt.tight_layout()
    
    output_path = output_dir / 'opd_trends.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path


def create_malaria_chart(df: pd.DataFrame, output_dir: Path) -> Path:
    """Create malaria surveillance chart"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    periods = df['period'].tolist()
    
    # Chart 1: Malaria testing and positivity
    if 'malaria_tested_numerator' in df.columns:
        tested = df['malaria_tested_numerator'].tolist()
        positive = df['malaria_positive_numerator'].tolist()
        
        x = range(len(periods))
        width = 0.35
        
        ax1.bar([i - width/2 for i in x], tested, width, 
                label='Tested', color=COLORS['info'], alpha=0.7)
        ax1.bar([i + width/2 for i in x], positive, width, 
                label='Positive', color=COLORS['danger'], alpha=0.7)
        
        ax1.set_title('Malaria Testing', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Week')
        ax1.set_ylabel('Number of Cases')
        ax1.set_xticks(x)
        ax1.set_xticklabels(periods, rotation=45, ha='right')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
    
    # Chart 2: Positivity rate
    if 'malaria_positivity_rate' in df.columns:
        rates = df['malaria_positivity_rate'].tolist()
        
        ax2.plot(periods, rates, marker='s', linestyle='-', 
                linewidth=2, color=COLORS['danger'])
        
        # Threshold lines
        ax2.axhline(y=0.05, color='green', linestyle='--', alpha=0.5, label='Normal (<5%)')
        ax2.axhline(y=0.10, color='orange', linestyle='--', alpha=0.5, label='Warning (>10%)')
        ax2.axhline(y=0.20, color='red', linestyle='--', alpha=0.5, label='Critical (>20%)')
        
        ax2.set_title('Malaria Positivity Rate', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Week')
        ax2.set_ylabel('Positivity Rate')
        ax2.set_xticklabels(periods, rotation=45, ha='right')
        ax2.set_ylim(0, max(0.5, max(rates) * 1.1))
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    output_path = output_dir / 'malaria_surveillance.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path


def create_maternal_health_chart(df: pd.DataFrame, output_dir: Path) -> Path:
    """Create maternal health chart"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    periods = df['period'].tolist()
    
    # Stacked bar chart for maternal services
    deliveries = df['institutional_deliveries'].tolist()
    anc = df['anc_contacts'].tolist()
    pnc = df['pnc_attendees'].tolist()
    fp = df['fp_clients'].tolist()
    
    x = range(len(periods))
    width = 0.2
    
    ax.bar([i - 1.5*width for i in x], deliveries, width, 
           label='Deliveries', color=COLORS['maternal'], alpha=0.8)
    ax.bar([i - 0.5*width for i in x], anc, width, 
           label='ANC', color='#5D9B9B', alpha=0.8)
    ax.bar([i + 0.5*width for i in x], pnc, width, 
           label='PNC', color='#B5C9C9', alpha=0.8)
    ax.bar([i + 1.5*width for i in x], fp, width, 
           label='FP', color='#E6B89C', alpha=0.8)
    
    ax.set_title('Maternal Health Services', fontsize=14, fontweight='bold')
    ax.set_xlabel('Week')
    ax.set_ylabel('Number of Clients')
    ax.set_xticks(x)
    ax.set_xticklabels(periods, rotation=45, ha='right')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    # Add ratio information as text
    total_deliveries = sum(deliveries)
    total_anc = sum(anc)
    if total_deliveries > 0:
        anc_per_delivery = total_anc / total_deliveries
        ax.text(0.02, 0.95, f'ANC per delivery: {anc_per_delivery:.1f}', 
                transform=ax.transAxes, fontsize=10,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    output_path = output_dir / 'maternal_health.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path


def create_child_health_chart(df: pd.DataFrame, output_dir: Path) -> Path:
    """Create child health chart"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    periods = df['period'].tolist()
    
    # Chart 1: Vaccinations
    if 'children_vaccinated_penta3' in df.columns:
        vaccinated = df['children_vaccinated_penta3'].tolist()
        
        ax1.bar(periods, vaccinated, color=COLORS['child'], alpha=0.7)
        ax1.set_title('Penta3 Vaccinations', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Week')
        ax1.set_ylabel('Number of Children')
        ax1.set_xticklabels(periods, rotation=45, ha='right')
        ax1.grid(True, alpha=0.3)
        
        # Add average line
        avg_vac = np.mean(vaccinated)
        ax1.axhline(y=avg_vac, color='darkgreen', linestyle='--', 
                   label=f'Average: {avg_vac:.1f}')
        ax1.legend()
    
    # Chart 2: Malnutrition
    if 'under5_sam' in df.columns and 'under5_mam' in df.columns:
        sam = df['under5_sam'].tolist()
        mam = df['under5_mam'].tolist()
        
        x = range(len(periods))
        width = 0.35
        
        ax2.bar([i - width/2 for i in x], sam, width, 
                label='SAM', color='#FF6B6B', alpha=0.8)
        ax2.bar([i + width/2 for i in x], mam, width, 
                label='MAM', color='#FFD93D', alpha=0.8)
        
        ax2.set_title('Malnutrition Cases (Under 5)', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Week')
        ax2.set_ylabel('Number of Children')
        ax2.set_xticks(x)
        ax2.set_xticklabels(periods, rotation=45, ha='right')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    output_path = output_dir / 'child_health.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path


def create_hiv_tb_chart(df: pd.DataFrame, output_dir: Path) -> Path:
    """Create HIV/TB services chart"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    periods = df['period'].tolist()
    
    # Chart 1: HIV testing
    if 'hiv_tested' in df.columns:
        hiv_tested = df['hiv_tested'].tolist()
        
        ax1.bar(periods, hiv_tested, color=COLORS['hiv'], alpha=0.7)
        ax1.set_title('HIV Testing', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Week')
        ax1.set_ylabel('Number Tested')
        ax1.set_xticklabels(periods, rotation=45, ha='right')
        ax1.grid(True, alpha=0.3)
        
        # Add cumulative
        cumulative = np.cumsum(hiv_tested)
        ax1_twin = ax1.twinx()
        ax1_twin.plot(periods, cumulative, color='darkorange', 
                     marker='o', linestyle='-', linewidth=2,
                     label='Cumulative')
        ax1_twin.set_ylabel('Cumulative', color='darkorange')
        ax1_twin.tick_params(axis='y', labelcolor='darkorange')
    
    # Chart 2: TB screening
    if 'tb_screened' in df.columns:
        tb_screened = df['tb_screened'].tolist()
        
        ax2.bar(periods, tb_screened, color=COLORS['tb'], alpha=0.7)
        ax2.set_title('TB Screening', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Week')
        ax2.set_ylabel('Number Screened')
        ax2.set_xticklabels(periods, rotation=45, ha='right')
        ax2.grid(True, alpha=0.3)
        
        # Calculate screening rate (TB screened / OPD visits)
        if 'opd_visits' in df.columns:
            opd = df['opd_visits'].tolist()
            rates = [t/o if o>0 else 0 for t, o in zip(tb_screened, opd)]
            
            ax2_twin = ax2.twinx()
            ax2_twin.plot(periods, rates, color='darkblue', 
                         marker='s', linestyle='--', linewidth=1.5,
                         label='% of OPD')
            ax2_twin.set_ylabel('% of OPD', color='darkblue')
            ax2_twin.tick_params(axis='y', labelcolor='darkblue')
    
    plt.tight_layout()
    
    output_path = output_dir / 'hiv_tb_services.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path


def create_performance_radar(df: pd.DataFrame, output_dir: Path) -> Path:
    """Create radar chart of key performance indicators"""
    # Calculate performance indicators
    indicators = calculate_performance_indicators_from_df(df)
    
    if not indicators:
        # Create empty chart with message
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.text(0.5, 0.5, 'Insufficient data for radar chart',
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        
        output_path = output_dir / 'performance_radar.png'
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        return output_path
    
    # Select indicators for radar
    radar_metrics = {
        'Malaria Testing': indicators.get('malaria_testing_rate', 0),
        'Inst. Delivery': indicators.get('institutional_delivery_rate', 0),
        'ANC Coverage': indicators.get('anc_coverage', 0),
        'PNC Coverage': indicators.get('pnc_coverage', 0),
        'HIV Testing': indicators.get('hiv_testing_rate', 0),
    }
    
    # Filter out zeros
    radar_metrics = {k: v for k, v in radar_metrics.items() if v > 0}
    
    if not radar_metrics:
        output_path = output_dir / 'performance_radar.png'
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        return output_path
    
    categories = list(radar_metrics.keys())
    values = list(radar_metrics.values())
    
    # Number of variables
    N = len(categories)
    
    # Create angles for each category
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    values += values[:1]  # Repeat first value to close the polygon
    angles += angles[:1]
    
    # Create plot
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    
    # Draw polygon
    ax.plot(angles, values, 'o-', linewidth=2, color=COLORS['primary'])
    ax.fill(angles, values, alpha=0.25, color=COLORS['primary'])
    
    # Set category labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11)
    
    # Set y-axis limits
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'])
    ax.set_rlabel_position(30)
    
    # Add title
    ax.set_title('Performance Indicators\n(% of target)', fontsize=14, fontweight='bold', pad=20)
    
    # Add target rings
    ax.plot(angles, [0.5] * len(angles), '--', color='gray', alpha=0.5, linewidth=0.5)
    ax.plot(angles, [0.75] * len(angles), '--', color='gray', alpha=0.5, linewidth=0.5)
    ax.plot(angles, [1.0] * len(angles), '--', color='gray', alpha=0.5, linewidth=0.5)
    
    plt.tight_layout()
    
    output_path = output_dir / 'performance_radar.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path


def create_data_quality_heatmap(df: pd.DataFrame, output_dir: Path) -> Path:
    """Create heatmap showing data quality (missing/zero values)"""
    # Select key metrics
    metrics = ['opd_visits', 'institutional_deliveries', 'anc_contacts', 
               'fp_clients', 'hiv_tested', 'children_vaccinated_penta3',
               'malaria_tested_numerator', 'tb_screened']
    
    # Filter to available metrics
    available_metrics = [m for m in metrics if m in df.columns]
    
    if not available_metrics:
        # Create empty chart
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No data for quality heatmap', 
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        
        output_path = output_dir / 'data_quality.png'
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        return output_path
    
    # Create matrix of zeros (0 = has data, 1 = missing/zero)
    quality_matrix = []
    
    for idx, row in df.iterrows():
        row_quality = []
        for metric in available_metrics:
            value = row[metric]
            if pd.isna(value) or value == 0:
                row_quality.append(1)  # Missing or zero
            else:
                row_quality.append(0)  # Has data
        quality_matrix.append(row_quality)
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, len(df) * 0.5 + 2))
    
    im = ax.imshow(quality_matrix, cmap='RdYlGn_r', aspect='auto', 
                   vmin=0, vmax=1, interpolation='nearest')
    
    # Set ticks
    ax.set_xticks(range(len(available_metrics)))
    ax.set_xticklabels(available_metrics, rotation=45, ha='right', fontsize=10)
    
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df['period'].tolist(), fontsize=9)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, ticks=[0, 1])
    cbar.ax.set_yticklabels(['Has Data', 'Missing/Zero'])
    
    ax.set_title('Data Quality Heatmap\n(Green = data present, Red = missing/zero)', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Add gridlines
    ax.set_xticks([x - 0.5 for x in range(len(available_metrics) + 1)], minor=True)
    ax.set_yticks([y - 0.5 for y in range(len(df) + 1)], minor=True)
    ax.grid(which='minor', color='black', linestyle='-', linewidth=0.5)
    
    plt.tight_layout()
    
    output_path = output_dir / 'data_quality.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path


def create_weekly_comparison(df: pd.DataFrame, output_dir: Path) -> Path:
    """Create comparison of last 4 weeks vs historical average"""
    if len(df) < 5:
        # Not enough data
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'Need at least 5 weeks of data for comparison',
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        
        output_path = output_dir / 'weekly_comparison.png'
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        return output_path
    
    # Get last 4 weeks
    last_4 = df.tail(4).copy()
    historical = df.head(len(df) - 4)
    
    metrics = ['opd_visits', 'institutional_deliveries', 'anc_contacts', 
               'fp_clients', 'hiv_tested']
    
    available_metrics = [m for m in metrics if m in df.columns]
    
    if not available_metrics:
        output_path = output_dir / 'weekly_comparison.png'
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        return output_path
    
    # Calculate historical averages
    historical_avg = {}
    for metric in available_metrics:
        historical_avg[metric] = historical[metric].mean()
    
    # Prepare data for plotting
    weeks = last_4['period'].tolist()
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for idx, metric in enumerate(available_metrics[:5]):  # Max 5 metrics
        ax = axes[idx]
        
        # Last 4 weeks values
        recent_values = last_4[metric].tolist()
        
        # Bar chart
        bars = ax.bar(weeks, recent_values, color=COLORS['primary'], alpha=0.7)
        
        # Add historical average line
        avg_value = historical_avg[metric]
        ax.axhline(y=avg_value, color='red', linestyle='--', 
                  linewidth=2, label=f'Historical Avg: {avg_value:.1f}')
        
        # Highlight bars above/below average
        for i, (bar, value) in enumerate(zip(bars, recent_values)):
            if value < avg_value * 0.8:
                bar.set_color(COLORS['danger'])
                bar.set_alpha(0.8)
            elif value < avg_value:
                bar.set_color(COLORS['warning'])
                bar.set_alpha(0.8)
            elif value > avg_value * 1.2:
                bar.set_color(COLORS['success'])
                bar.set_alpha(0.8)
        
        ax.set_title(f'{metric.replace("_", " ").title()}', fontsize=11)
        ax.set_ylabel('Count')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    # Hide unused subplot
    for idx in range(len(available_metrics), 5):
        axes[idx].axis('off')
    
    plt.suptitle('Last 4 Weeks vs Historical Average', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    output_path = output_dir / 'weekly_comparison.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path


def create_distribution_plots(df: pd.DataFrame, output_dir: Path) -> Path:
    """Create distribution histograms for key metrics"""
    metrics = ['opd_visits', 'institutional_deliveries', 'anc_contacts', 'hiv_tested']
    available_metrics = [m for m in metrics if m in df.columns]
    
    if not available_metrics:
        # Create empty chart
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No data for distribution plots',
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        
        output_path = output_dir / 'distributions.png'
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        return output_path
    
    # Determine grid size
    n_metrics = len(available_metrics)
    n_cols = min(3, n_metrics)
    n_rows = (n_metrics + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows))
    
    # Flatten axes for easier indexing
    if n_rows == 1 and n_cols == 1:
        axes = np.array([axes])
    axes = axes.flatten()
    
    for idx, metric in enumerate(available_metrics):
        ax = axes[idx]
        
        values = df[metric].dropna()
        
        # Histogram
        n, bins, patches = ax.hist(values, bins='auto', edgecolor='black',
                                   color=COLORS['primary'], alpha=0.7)
        
        # Add vertical lines for statistics
        mean_val = values.mean()
        median_val = values.median()
        
        ax.axvline(mean_val, color='red', linestyle='--', 
                  linewidth=2, label=f'Mean: {mean_val:.1f}')
        ax.axvline(median_val, color='green', linestyle='--', 
                  linewidth=2, label=f'Median: {median_val:.1f}')
        
        ax.set_title(f'{metric.replace("_", " ").title()} Distribution', fontsize=12)
        ax.set_xlabel('Value')
        ax.set_ylabel('Frequency')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    
    # Hide unused subplots
    for idx in range(len(available_metrics), len(axes)):
        axes[idx].axis('off')
    
    plt.suptitle('Distribution of Key Metrics', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    output_path = output_dir / 'distributions.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path


def create_combined_dashboard(df: pd.DataFrame, facility_name: str, 
                              output_dir: Path) -> Path:
    """Create a combined dashboard with multiple charts"""
    fig = plt.figure(figsize=(20, 24))
    
    # Create grid layout
    gs = fig.add_gridspec(6, 3, hspace=0.3, wspace=0.3)
    
    # Title
    fig.suptitle(f'{facility_name} - Health Facility Dashboard\n'
                f'Data from {df["period"].iloc[0]} to {df["period"].iloc[-1]}', 
                fontsize=18, fontweight='bold', y=0.98)
    
    # 1. Summary cards (top row, all columns)
    ax_summary = fig.add_subplot(gs[0, :])
    ax_summary.axis('off')
    
    # Create summary cards
    total_opd = int(df['opd_visits'].sum())
    total_deliveries = int(df['institutional_deliveries'].sum())
    total_anc = int(df['anc_contacts'].sum())
    
    cards = [
        {'title': 'Total OPD', 'value': f'{total_opd:,}', 'color': COLORS['opd']},
        {'title': 'Deliveries', 'value': f'{total_deliveries}', 'color': COLORS['maternal']},
        {'title': 'ANC Contacts', 'value': f'{total_anc}', 'color': COLORS['maternal']},
        {'title': 'Weeks Reported', 'value': f'{len(df)}', 'color': COLORS['info']},
    ]
    
    for i, card in enumerate(cards):
        x = 0.1 + (i * 0.2)
        y = 0.5
        
        rect = plt.Rectangle((x-0.08, y-0.3), 0.16, 0.4, 
                             facecolor=card['color'], alpha=0.1,
                             edgecolor=card['color'], linewidth=2,
                             transform=fig.transFigure)
        fig.patches.append(rect)
        
        ax_summary.text(x, y, card['title'], ha='center', va='center', 
                       fontsize=12, fontweight='bold', transform=fig.transFigure)
        ax_summary.text(x, y-0.15, card['value'], ha='center', va='center', 
                       fontsize=16, fontweight='bold', color=card['color'],
                       transform=fig.transFigure)
    
    # 2. OPD Trends
    ax_opd = fig.add_subplot(gs[1, :2])
    periods = df['period'].tolist()
    ax_opd.plot(periods, df['opd_visits'], marker='o', color=COLORS['opd'])
    ax_opd.set_title('OPD Visits Over Time', fontsize=12, fontweight='bold')
    ax_opd.set_xticklabels(periods, rotation=45, ha='right')
    ax_opd.grid(True, alpha=0.3)
    
    # 3. Malaria
    ax_malaria = fig.add_subplot(gs[1, 2])
    if 'malaria_positive_numerator' in df.columns:
        ax_malaria.bar(periods, df['malaria_positive_numerator'], 
                      color=COLORS['danger'])
        ax_malaria.set_title('Malaria Cases', fontsize=12, fontweight='bold')
        ax_malaria.set_xticklabels(periods, rotation=45, ha='right')
    
    # 4. Deliveries
    ax_deliveries = fig.add_subplot(gs[2, 0])
    ax_deliveries.bar(periods, df['institutional_deliveries'], 
                      color=COLORS['maternal'])
    ax_deliveries.set_title('Institutional Deliveries', fontsize=12, fontweight='bold')
    ax_deliveries.set_xticklabels(periods, rotation=45, ha='right')
    
    # 5. ANC
    ax_anc = fig.add_subplot(gs[2, 1])
    ax_anc.bar(periods, df['anc_contacts'], color='#5D9B9B')
    ax_anc.set_title('ANC Contacts', fontsize=12, fontweight='bold')
    ax_anc.set_xticklabels(periods, rotation=45, ha='right')
    
    # 6. Family Planning
    ax_fp = fig.add_subplot(gs[2, 2])
    ax_fp.bar(periods, df['fp_clients'], color='#E6B89C')
    ax_fp.set_title('Family Planning', fontsize=12, fontweight='bold')
    ax_fp.set_xticklabels(periods, rotation=45, ha='right')
    
    # 7. HIV Testing
    ax_hiv = fig.add_subplot(gs[3, 0])
    ax_hiv.bar(periods, df['hiv_tested'], color=COLORS['hiv'])
    ax_hiv.set_title('HIV Testing', fontsize=12, fontweight='bold')
    ax_hiv.set_xticklabels(periods, rotation=45, ha='right')
    
    # 8. Vaccinations
    ax_vac = fig.add_subplot(gs[3, 1])
    ax_vac.bar(periods, df['children_vaccinated_penta3'], color=COLORS['child'])
    ax_vac.set_title('Penta3 Vaccinations', fontsize=12, fontweight='bold')
    ax_vac.set_xticklabels(periods, rotation=45, ha='right')
    
    # 9. TB Screening
    ax_tb = fig.add_subplot(gs[3, 2])
    ax_tb.bar(periods, df['tb_screened'], color=COLORS['tb'])
    ax_tb.set_title('TB Screening', fontsize=12, fontweight='bold')
    ax_tb.set_xticklabels(periods, rotation=45, ha='right')
    
    # 10. Performance Radar (if we have indicators)
    ax_radar = fig.add_subplot(gs[4:6, :])
    
    indicators = calculate_performance_indicators_from_df(df)
    if indicators:
        radar_metrics = {
            'Malaria Testing': indicators.get('malaria_testing_rate', 0),
            'Inst. Delivery': indicators.get('institutional_delivery_rate', 0),
            'ANC Coverage': indicators.get('anc_coverage', 0),
            'PNC Coverage': indicators.get('pnc_coverage', 0),
            'HIV Testing': indicators.get('hiv_testing_rate', 0),
        }
        
        # Filter out zeros
        radar_metrics = {k: v for k, v in radar_metrics.items() if v > 0}
        
        if radar_metrics:
            categories = list(radar_metrics.keys())
            values = list(radar_metrics.values())
            
            N = len(categories)
            angles = [n / float(N) * 2 * np.pi for n in range(N)]
            values += values[:1]
            angles += angles[:1]
            
            ax_radar.remove()  # Remove the subplot we added
            ax_radar = fig.add_subplot(gs[4:6, :], projection='polar')
            
            ax_radar.plot(angles, values, 'o-', linewidth=2, color=COLORS['primary'])
            ax_radar.fill(angles, values, alpha=0.25, color=COLORS['primary'])
            ax_radar.set_xticks(angles[:-1])
            ax_radar.set_xticklabels(categories, fontsize=10)
            ax_radar.set_ylim(0, 1)
            ax_radar.set_title('Performance Indicators', fontsize=12, fontweight='bold', pad=20)
        else:
            ax_radar.text(0.5, 0.5, 'Insufficient data for radar chart',
                         ha='center', va='center', transform=ax_radar.transAxes)
            ax_radar.axis('off')
    else:
        ax_radar.text(0.5, 0.5, 'Insufficient data for radar chart',
                     ha='center', va='center', transform=ax_radar.transAxes)
        ax_radar.axis('off')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    output_path = output_dir / 'combined_dashboard.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path


# ======================
# FACILITY COMPARISON CHARTS
# ======================

def create_facility_comparison_chart(facilities_data: Dict[int, Dict],
                                     output_dir: Path) -> Path:
    """
    Create comparison chart for multiple facilities
    
    Args:
        facilities_data: Dictionary with facility_id -> {name, metrics}
    """
    if not facilities_data:
        return None
    
    # Prepare data
    facility_names = []
    opd_values = []
    delivery_values = []
    anc_values = []
    
    for fid, data in facilities_data.items():
        facility_names.append(data['name'])
        opd_values.append(data.get('opd_visits', 0))
        delivery_values.append(data.get('institutional_deliveries', 0))
        anc_values.append(data.get('anc_contacts', 0))
    
    # Create chart
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    x = range(len(facility_names))
    width = 0.25
    
    # Top left: OPD visits
    ax = axes[0, 0]
    ax.bar(x, opd_values, width, color=COLORS['opd'])
    ax.set_title('Total OPD Visits', fontsize=12, fontweight='bold')
    ax.set_xlabel('Facility')
    ax.set_ylabel('Count')
    ax.set_xticks(x)
    ax.set_xticklabels(facility_names, rotation=45, ha='right')
    
    # Top right: Deliveries
    ax = axes[0, 1]
    ax.bar(x, delivery_values, width, color=COLORS['maternal'])
    ax.set_title('Institutional Deliveries', fontsize=12, fontweight='bold')
    ax.set_xlabel('Facility')
    ax.set_ylabel('Count')
    ax.set_xticks(x)
    ax.set_xticklabels(facility_names, rotation=45, ha='right')
    
    # Bottom left: ANC contacts
    ax = axes[1, 0]
    ax.bar(x, anc_values, width, color='#5D9B9B')
    ax.set_title('ANC Contacts', fontsize=12, fontweight='bold')
    ax.set_xlabel('Facility')
    ax.set_ylabel('Count')
    ax.set_xticks(x)
    ax.set_xticklabels(facility_names, rotation=45, ha='right')
    
    # Bottom right: Combined comparison
    ax = axes[1, 1]
    ax.bar([i - width for i in x], opd_values, width, label='OPD', color=COLORS['opd'])
    ax.bar(x, delivery_values, width, label='Deliveries', color=COLORS['maternal'])
    ax.bar([i + width for i in x], anc_values, width, label='ANC', color='#5D9B9B')
    ax.set_title('Combined Comparison', fontsize=12, fontweight='bold')
    ax.set_xlabel('Facility')
    ax.set_ylabel('Count')
    ax.set_xticks(x)
    ax.set_xticklabels(facility_names, rotation=45, ha='right')
    ax.legend()
    
    plt.suptitle('Facility Comparison Dashboard', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    output_path = output_dir / 'facility_comparison.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path


def create_ranking_chart(facilities_data: Dict[int, Dict],
                         metric: str,
                         output_dir: Path,
                         title: str = None) -> Path:
    """
    Create ranking bar chart for a specific metric
    """
    if not facilities_data:
        return None
    
    # Sort facilities by metric
    sorted_facilities = sorted(facilities_data.items(), 
                               key=lambda x: x[1].get(metric, 0), 
                               reverse=True)
    
    names = [data['name'] for _, data in sorted_facilities]
    values = [data.get(metric, 0) for _, data in sorted_facilities]
    
    # Create horizontal bar chart for better readability
    fig, ax = plt.subplots(figsize=(10, max(6, len(names) * 0.4)))
    
    y_pos = np.arange(len(names))
    bars = ax.barh(y_pos, values, color=COLORS['primary'])
    
    # Color the top 3
    for i, bar in enumerate(bars[:3]):
        bar.set_color(COLORS['success'])
    
    # Color the bottom 3
    for i, bar in enumerate(bars[-3:]):
        bar.set_color(COLORS['danger'])
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.invert_yaxis()  # Labels read top-to-bottom
    ax.set_xlabel('Count')
    
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold')
    else:
        ax.set_title(f'Facility Ranking - {metric.replace("_", " ").title()}', 
                    fontsize=14, fontweight='bold')
    
    # Add value labels
    for i, (bar, value) in enumerate(zip(bars, values)):
        ax.text(value + (max(values) * 0.01), i, f' {value}', 
                va='center', fontsize=9)
    
    plt.tight_layout()
    
    output_path = output_dir / f'ranking_{metric}.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path


# ======================
# DISTRICT DASHBOARD
# ======================

def create_district_dashboard(district_name: str,
                              facilities_data: Dict[int, Dict],
                              output_dir: Path) -> Path:
    """
    Create district-level dashboard
    """
    fig = plt.figure(figsize=(20, 24))
    
    # Create grid
    gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)
    
    # Title
    fig.suptitle(f'{district_name} District - Health Dashboard\n'
                f'Facilities Reporting: {len(facilities_data)}', 
                fontsize=18, fontweight='bold', y=0.98)
    
    # 1. Summary stats
    ax_summary = fig.add_subplot(gs[0, :])
    ax_summary.axis('off')
    
    total_opd = sum(data.get('opd_visits', 0) for data in facilities_data.values())
    total_deliveries = sum(data.get('institutional_deliveries', 0) for data in facilities_data.values())
    total_anc = sum(data.get('anc_contacts', 0) for data in facilities_data.values())
    
    cards = [
        {'title': 'Total OPD', 'value': f'{total_opd:,}', 'color': COLORS['opd']},
        {'title': 'Deliveries', 'value': f'{total_deliveries:,}', 'color': COLORS['maternal']},
        {'title': 'ANC Contacts', 'value': f'{total_anc:,}', 'color': COLORS['maternal']},
        {'title': 'Facilities', 'value': f'{len(facilities_data)}', 'color': COLORS['info']},
    ]
    
    for i, card in enumerate(cards):
        x = 0.1 + (i * 0.2)
        y = 0.5
        
        rect = plt.Rectangle((x-0.08, y-0.3), 0.16, 0.4, 
                             facecolor=card['color'], alpha=0.1,
                             edgecolor=card['color'], linewidth=2,
                             transform=fig.transFigure)
        fig.patches.append(rect)
        
        ax_summary.text(x, y, card['title'], ha='center', va='center', 
                       fontsize=12, fontweight='bold', transform=fig.transFigure)
        ax_summary.text(x, y-0.15, card['value'], ha='center', va='center', 
                       fontsize=16, fontweight='bold', color=card['color'],
                       transform=fig.transFigure)
    
    # 2. Top facilities by OPD
    ax_top_opd = fig.add_subplot(gs[1, 0])
    sorted_opd = sorted(facilities_data.items(), key=lambda x: x[1].get('opd_visits', 0), reverse=True)[:5]
    names = [data['name'][:15] for _, data in sorted_opd]  # Truncate long names
    values = [data.get('opd_visits', 0) for _, data in sorted_opd]
    
    ax_top_opd.barh(names, values, color=COLORS['opd'])
    ax_top_opd.set_title('Top 5 - OPD Visits', fontsize=12, fontweight='bold')
    ax_top_opd.set_xlabel('Count')
    
    # 3. Top facilities by Deliveries
    ax_top_del = fig.add_subplot(gs[1, 1])
    sorted_del = sorted(facilities_data.items(), key=lambda x: x[1].get('institutional_deliveries', 0), reverse=True)[:5]
    names = [data['name'][:15] for _, data in sorted_del]
    values = [data.get('institutional_deliveries', 0) for _, data in sorted_del]
    
    ax_top_del.barh(names, values, color=COLORS['maternal'])
    ax_top_del.set_title('Top 5 - Deliveries', fontsize=12, fontweight='bold')
    ax_top_del.set_xlabel('Count')
    
    # 4. Bottom facilities (needs improvement)
    ax_bottom = fig.add_subplot(gs[1, 2])
    sorted_bottom = sorted(facilities_data.items(), key=lambda x: x[1].get('opd_visits', 0))[:5]
    names = [data['name'][:15] for _, data in sorted_bottom]
    values = [data.get('opd_visits', 0) for _, data in sorted_bottom]
    
    ax_bottom.barh(names, values, color=COLORS['danger'])
    ax_bottom.set_title('Needs Improvement - OPD', fontsize=12, fontweight='bold')
    ax_bottom.set_xlabel('Count')
    
    # 5. Distribution of OPD visits
    ax_dist = fig.add_subplot(gs[2, 0])
    opd_values = [data.get('opd_visits', 0) for data in facilities_data.values()]
    ax_dist.hist(opd_values, bins='auto', edgecolor='black', color=COLORS['primary'])
    ax_dist.set_title('Distribution of OPD Visits', fontsize=12, fontweight='bold')
    ax_dist.set_xlabel('OPD Visits')
    ax_dist.set_ylabel('Number of Facilities')
    
    # 6. Scatter plot: Deliveries vs ANC
    ax_scatter = fig.add_subplot(gs[2, 1:])
    deliveries = [data.get('institutional_deliveries', 0) for data in facilities_data.values()]
    anc = [data.get('anc_contacts', 0) for data in facilities_data.values()]
    names = [data['name'] for data in facilities_data.values()]
    
    scatter = ax_scatter.scatter(deliveries, anc, c=range(len(deliveries)), 
                                 cmap='viridis', s=100, alpha=0.7)
    ax_scatter.set_xlabel('Institutional Deliveries')
    ax_scatter.set_ylabel('ANC Contacts')
    ax_scatter.set_title('Deliveries vs ANC by Facility', fontsize=12, fontweight='bold')
    
    # Add labels for outliers
    for i, name in enumerate(names):
        if deliveries[i] > np.percentile(deliveries, 90) or anc[i] > np.percentile(anc, 90):
            ax_scatter.annotate(name[:10], (deliveries[i], anc[i]), 
                               fontsize=8, alpha=0.7)
    
    plt.colorbar(scatter, ax=ax_scatter, label='Facility Index')
    
    # 7. Summary table
    ax_table = fig.add_subplot(gs[3, :])
    ax_table.axis('off')
    
    # Prepare table data
    table_data = []
    for fid, data in list(facilities_data.items())[:10]:  # Top 10
        table_data.append([
            data['name'][:20],
            data.get('opd_visits', 0),
            data.get('institutional_deliveries', 0),
            data.get('anc_contacts', 0),
            data.get('hiv_tested', 0)
        ])
    
    columns = ['Facility', 'OPD', 'Deliveries', 'ANC', 'HIV Tested']
    
    table = ax_table.table(cellText=table_data, colLabels=columns,
                          cellLoc='center', loc='center',
                          colColours=[COLORS['light']] * 5)
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    
    ax_table.set_title('Facility Summary (Top 10)', fontsize=12, fontweight='bold', pad=20)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    output_path = output_dir / f'{district_name}_dashboard.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path


# ======================
# TREND CHARTS
# ======================

def create_trend_chart(facility_name: str,
                       df: pd.DataFrame,
                       metrics: List[str],
                       output_dir: Path) -> Path:
    """
    Create multi-metric trend chart
    """
    if df.empty:
        return None
    
    periods = df['period'].tolist()
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    colors = [COLORS['opd'], COLORS['maternal'], COLORS['child'], 
              COLORS['hiv'], COLORS['tb'], COLORS['warning']]
    
    for idx, metric in enumerate(metrics):
        if metric in df.columns:
            values = df[metric].tolist()
            ax.plot(periods, values, marker='o', linewidth=2,
                   color=colors[idx % len(colors)],
                   label=metric.replace('_', ' ').title())
    
    ax.set_title(f'{facility_name} - Key Metrics Trends', fontsize=14, fontweight='bold')
    ax.set_xlabel('Week')
    ax.set_ylabel('Count')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    if len(periods) > 10:
        plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    
    output_path = output_dir / f'{facility_name}_trends.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path


# ======================
# PLOTLY INTERACTIVE CHARTS
# ======================

def create_plotly_dashboard(df: pd.DataFrame, 
                            facility_name: str,
                            output_dir: Path) -> Path:
    """
    Create interactive Plotly dashboard (HTML file)
    """
    # Create subplots
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=('OPD Visits', 'Malaria Cases', 
                       'Institutional Deliveries', 'ANC Contacts',
                       'HIV Testing', 'Penta3 Vaccinations'),
        specs=[[{'secondary_y': False}, {'secondary_y': False}],
               [{'secondary_y': False}, {'secondary_y': False}],
               [{'secondary_y': False}, {'secondary_y': False}]]
    )
    
    periods = df['period'].tolist()
    
    # 1. OPD Visits
    fig.add_trace(
        go.Scatter(x=periods, y=df['opd_visits'],
                  mode='lines+markers',
                  name='OPD Visits',
                  line=dict(color=COLORS['opd'], width=2)),
        row=1, col=1
    )
    
    # 2. Malaria cases
    if 'malaria_positive_numerator' in df.columns:
        fig.add_trace(
            go.Bar(x=periods, y=df['malaria_positive_numerator'],
                   name='Malaria Positive',
                   marker_color=COLORS['danger']),
            row=1, col=2
        )
    
    # 3. Deliveries
    fig.add_trace(
        go.Bar(x=periods, y=df['institutional_deliveries'],
               name='Deliveries',
               marker_color=COLORS['maternal']),
        row=2, col=1
    )
    
    # 4. ANC
    fig.add_trace(
        go.Bar(x=periods, y=df['anc_contacts'],
               name='ANC Contacts',
               marker_color='#5D9B9B'),
        row=2, col=2
    )
    
    # 5. HIV Testing
    fig.add_trace(
        go.Bar(x=periods, y=df['hiv_tested'],
               name='HIV Testing',
               marker_color=COLORS['hiv']),
        row=3, col=1
    )
    
    # 6. Vaccinations
    fig.add_trace(
        go.Bar(x=periods, y=df['children_vaccinated_penta3'],
               name='Penta3 Vaccinations',
               marker_color=COLORS['child']),
        row=3, col=2
    )
    
    # Update layout
    fig.update_layout(
        title_text=f'{facility_name} - Interactive Dashboard',
        showlegend=True,
        height=900,
        hovermode='x unified'
    )
    
    # Update axes
    fig.update_xaxes(title_text="Week", tickangle=45)
    fig.update_yaxes(title_text="Count")
    
    # Save as HTML
    output_path = output_dir / 'interactive_dashboard.html'
    fig.write_html(str(output_path))
    
    return output_path


# ======================
# UTILITY FUNCTIONS
# ======================

def calculate_performance_indicators_from_df(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate performance indicators from DataFrame"""
    indicators = {}
    
    # Malaria testing rate
    if 'malaria_suspected_numerator' in df.columns and 'malaria_tested_numerator' in df.columns:
        total_suspected = df['malaria_suspected_numerator'].sum()
        total_tested = df['malaria_tested_numerator'].sum()
        
        if total_suspected > 0:
            indicators['malaria_testing_rate'] = total_tested / total_suspected
    
    # Institutional delivery rate
    if 'institutional_deliveries' in df.columns and 'home_deliveries' in df.columns:
        total_deliveries = df['institutional_deliveries'].sum() + df['home_deliveries'].sum()
        if total_deliveries > 0:
            indicators['institutional_delivery_rate'] = df['institutional_deliveries'].sum() / total_deliveries
    
    # ANC coverage (simplified)
    if 'anc_contacts' in df.columns and 'institutional_deliveries' in df.columns:
        total_deliveries = df['institutional_deliveries'].sum()
        expected_anc = total_deliveries * 4
        if expected_anc > 0:
            indicators['anc_coverage'] = min(df['anc_contacts'].sum() / expected_anc, 1.0)
    
    # PNC coverage
    if 'pnc_attendees' in df.columns and 'institutional_deliveries' in df.columns:
        total_deliveries = df['institutional_deliveries'].sum()
        if total_deliveries > 0:
            indicators['pnc_coverage'] = df['pnc_attendees'].sum() / total_deliveries
    
    # HIV testing rate (vs OPD)
    if 'hiv_tested' in df.columns and 'opd_visits' in df.columns:
        total_opd = df['opd_visits'].sum()
        if total_opd > 0:
            indicators['hiv_testing_rate'] = df['hiv_tested'].sum() / total_opd
    
    return indicators


def fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 string for embedding in HTML"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=80, bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str

def generate_heatmap(data, output_dir, title="Heatmap"):
    """
    Generate a heatmap visualization
    
    Args:
        data: DataFrame or matrix for heatmap
        output_dir: Output directory
        title: Chart title
        
    Returns:
        Path to generated heatmap
    """
    import seaborn as sns
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    if isinstance(data, pd.DataFrame):
        # If data is a DataFrame with numeric columns, create correlation heatmap
        numeric_cols = data.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 1:
            corr = data[numeric_cols].corr()
            sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, ax=ax)
            ax.set_title(f'{title} - Correlation Heatmap')
        else:
            # Otherwise create a simple heatmap of the values
            sns.heatmap(data.select_dtypes(include=['number']).values, 
                       annot=True, cmap='YlGnBu', ax=ax)
            ax.set_title(title)
    else:
        # Assume data is a 2D array/list
        sns.heatmap(data, annot=True, cmap='YlGnBu', ax=ax)
        ax.set_title(title)
    
    output_path = output_dir / 'heatmap.png'
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path
# ======================
# MAIN TEST FUNCTION
# ======================

if __name__ == "__main__":
    # Test with sample data
    from health_parser import parse_health_report
    
    # Create sample reports
    reports = []
    
    for week in range(9, 20):
        sample_text = f"""
        Matotwe rhc
        Week {week}
        Malaria suspected 5/10
        Tested 8/10
        Positive 2/8
        OPD visits {40 + week}
        Institutional deliveries {3 + (week % 3)}
        ANC contacts {5 + week}
        FP clients {7 + week}
        HIV tested {2 + week}
        Children vaccinated penta3 {1 + (week % 2)}
        """
        
        report = parse_health_report(sample_text)
        report.facility_id = 1
        reports.append(report)
    
    # Create output directory
    test_dir = Path('./test_visuals')
    test_dir.mkdir(exist_ok=True)
    
    # Generate dashboard
    charts = generate_facility_dashboard('Matotwe RHC', reports, test_dir)
    
    print(f"Generated {len(charts)} charts in {test_dir}")
    
    # Test facility comparison
    facilities_data = {
        1: {'name': 'Matotwe RHC', 'opd_visits': 450, 'institutional_deliveries': 25, 'anc_contacts': 120},
        2: {'name': 'Maurice Nyagumbo', 'opd_visits': 380, 'institutional_deliveries': 18, 'anc_contacts': 95},
        3: {'name': 'Mayo 1 RHC', 'opd_visits': 520, 'institutional_deliveries': 32, 'anc_contacts': 145},
        4: {'name': 'Chikobvore', 'opd_visits': 290, 'institutional_deliveries': 12, 'anc_contacts': 68},
    }
    
    comparison_chart = create_facility_comparison_chart(facilities_data, test_dir)
    print(f"Generated comparison chart: {comparison_chart}")
    
    ranking_chart = create_ranking_chart(facilities_data, 'opd_visits', test_dir, 'OPD Visits Ranking')
    print(f"Generated ranking chart: {ranking_chart}")
    
    # Test district dashboard
    district_chart = create_district_dashboard('Test District', facilities_data, test_dir)
    print(f"Generated district dashboard: {district_chart}")