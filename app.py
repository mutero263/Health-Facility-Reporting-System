import os
import json
import logging
import uuid
import io
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import pandas as pd

from fastapi import FastAPI, File, UploadFile, Request, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
# SessionMiddleware is kept if you ever want login back, but routes are open
from starlette.middleware.sessions import SessionMiddleware 

# Local imports
from health_parser import parse_health_report, HealthReport
from health_analyzer import (
    analyze_weekly_data,
    calculate_facility_stats,
    detect_anomalies,
    get_facility_trends,
    compare_facilities,
    generate_alerts
)
from health_visualizer import (
    create_facility_comparison_chart,
    create_trend_chart,
    generate_facility_dashboard,
    create_district_dashboard,
    create_ranking_chart
)
from database import (
    init_db,
    get_db_connection,
    save_weekly_report,
    get_facility_reports,
    get_all_facilities,
    get_facility_by_id,
    create_facility,
    update_facility,
    get_alerts,
    resolve_alert,
    get_weekly_summary
)
from models import (
    Facility,
    WeeklyReport,
    User,
    Alert,
    ReportSummary,
    FacilityComparison
)
from utils import (
    validate_report_data,
    format_metrics_display,
    get_week_options,  # Fixed name
    save_uploaded_file,
    cleanup_old_files
)
# Auth imports removed for Public Mode, or keep if you want to re-enable login later
# from auth import (...) 

from config import (
    DATABASE_PATH,
    UPLOAD_DIR,      # Fixed name
    STATIC_DIR,      # Fixed name
    VISUALS_DIR,     # Fixed name
    SECRET_KEY,
    ALERT_THRESHOLDS,
    FACILITY_TYPES,
    REPORT_SECTIONS
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create necessary directories
for folder in [UPLOAD_DIR, STATIC_DIR, VISUALS_DIR]:
    os.makedirs(folder, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(title="Health Facility Reporting System", version="1.0.0")

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep SessionMiddleware just in case, but routes don't enforce login
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="health_session",
    max_age=24 * 60 * 60,
    same_site="lax"
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/visuals", StaticFiles(directory=VISUALS_DIR), name="visuals")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database"""
    init_db()
    logger.info("Health Facility Reporting System started (Public Mode)")

# Cleanup old files periodically
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup old temporary files"""
    # Ensure cleanup_old_files accepts the correct arguments
    try:
        cleanup_old_files(days=7) 
    except TypeError:
        # Fallback if function signature differs
        cleanup_old_files(UPLOAD_DIR, days=7)
    logger.info("Cleanup completed")

# ======================
# PUBLIC ROUTES (No Login Required)
# ======================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page with public overview"""
    conn = get_db_connection()
    facilities = get_all_facilities(conn)
    summary = get_weekly_summary(conn)
    conn.close()
    
    stats = {
        'total_facilities': len(facilities) if facilities else 0,
        'total_reports': summary.get('facilities_reporting', 0) if summary else 0
    }
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "current_year": datetime.now().year,
            "now": datetime.now(),
            "stats": stats
        }
    )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main public dashboard"""
    conn = get_db_connection()
    summary = get_weekly_summary(conn)
    facilities = get_all_facilities(conn)
    alerts = get_alerts(conn, limit=10)
    
    # Prepare chart data
    facilities_dict = {}
    if facilities:
        for f in facilities[:10]:
            facilities_dict[f['id']] = {
                'name': f['name'],
                'opd_visits': f.get('opd_visits', 0),
                'institutional_deliveries': f.get('institutional_deliveries', 0),
                'anc_contacts': f.get('anc_contacts', 0)
            }
    
    chart_path = None
    if facilities_dict:
        chart_path = create_facility_comparison_chart(facilities_dict, Path(VISUALS_DIR))
        if chart_path:
            chart_path = str(chart_path)
    
    conn.close()
    
    # Prepare stats
    stats = {
        'total_facilities': len(facilities) if facilities else 0,
        'active_facilities': len([f for f in facilities if f.get('active', True)]) if facilities else 0,
        'facility_change': 0,
        'total_reports': summary.get('facilities_reporting', 0) if summary else 0,
        'this_week_reports': summary.get('facilities_reporting', 0) if summary else 0,
        'report_change': 0,
        'total_opd': summary.get('total_opd', 0) if summary else 0,
        'opd_change': 0,
        'active_alerts': len(alerts) if alerts else 0,
        'critical_alerts': len([a for a in alerts if a.get('severity') == 'critical']) if alerts else 0
    }
    
    # Prepare KPI data
    kpi = {
        'reporting_rate': 85,
        'institutional_delivery_rate': 78,
        'malaria_positivity': 8,
        'anc_coverage': 72,
        'penta3_coverage': 88,
        'data_quality': 92
    }
    
    current_date = datetime.now()
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "summary": summary,
            "facilities": facilities[:10] if facilities else [],
            "alerts": alerts[:5] if alerts else [],
            "chart_path": chart_path,
            "current_week": datetime.now().isocalendar()[1],
            "current_date": current_date,
            "stats": stats,
            "kpi": kpi,
            "alert_count": len(alerts) if alerts else 0,
            "period": request.query_params.get("period", "week"),
            "current_year": datetime.now().year,
            "now": datetime.now()
        }
    )

@app.get("/facilities", response_class=HTMLResponse)
async def list_facilities(request: Request):
    """List all facilities (Public)"""
    conn = get_db_connection()
    facilities = get_all_facilities(conn)
    conn.close()
    
    districts = list(set([f.get('district', '') for f in facilities if f.get('district')]))
    
    # Mock stats for template
    stats = {
        'total_facilities': len(facilities),
        'new_facilities': 0,
        'active_facilities': len([f for f in facilities if f.get('active', True)]),
        'active_percentage': 100,
        'reporting_this_week': 0,
        'reporting_change': 0,
        'total_population': sum([f.get('catchment_population', 0) for f in facilities])
    }
    
    return templates.TemplateResponse(
        "facility_list.html",
        {
            "request": request,
            "facilities": facilities,
            "facility_types": FACILITY_TYPES,
            "districts": districts,
            "selected_district": request.query_params.get("district"),
            "selected_type": request.query_params.get("type"),
            "selected_status": request.query_params.get("status"),
            "search_query": request.query_params.get("search", ""),
            "page": int(request.query_params.get("page", 1)),
            "total_pages": max(1, (len(facilities) + 19) // 20),
            "view": request.query_params.get("view", "grid"),
            "stats": stats,
            "current_year": datetime.now().year,
            "now": datetime.now()
        }
    )

@app.get("/facilities/add", response_class=HTMLResponse)
async def add_facility_page(request: Request):
    """Add new facility form (Open)"""
    return templates.TemplateResponse(
        "facility_form.html",
        {
            "request": request,
            "facility": None,
            "facility_types": FACILITY_TYPES,
            "current_year": datetime.now().year,
            "now": datetime.now()
        }
    )

@app.post("/facilities/add")
async def add_facility(
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    district: str = Form(...),
    province: str = Form(...),
    catchment_population: int = Form(0),
    latitude: float = Form(None),
    longitude: float = Form(None)
):
    """Handle add facility form"""
    facility_dict = {
        'name': name,
        'type': type,
        'district': district,
        'province': province,
        'catchment_population': catchment_population,
        'latitude': latitude,
        'longitude': longitude,
        'active': True,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    conn = get_db_connection()
    facility_id = create_facility(conn, facility_dict)
    conn.close()
    
    return RedirectResponse(url=f"/facilities/{facility_id}", status_code=302)

@app.get("/facilities/{facility_id}", response_class=HTMLResponse)
async def view_facility(request: Request, facility_id: int):
    """View facility details and reports (Public)"""
    conn = get_db_connection()
    facility = get_facility_by_id(conn, facility_id)
    reports = get_facility_reports(conn, facility_id, limit=24)
    
    if not facility:
        conn.close()
        raise HTTPException(status_code=404, detail="Facility not found")
    
    chart_path = None
    if reports:
        df = pd.DataFrame(reports)
        chart_path = create_trend_chart(
            facility['name'],
            df,
            ['opd_visits', 'institutional_deliveries', 'anc_contacts'],
            Path(VISUALS_DIR) / f"facility_{facility_id}"
        )
        if chart_path:
            chart_path = str(chart_path)
    
    conn.close()
    
    return templates.TemplateResponse(
        "facility_detail.html",
        {
            "request": request,
            "facility": facility,
            "reports": reports,
            "chart_path": chart_path,
            "weeks": get_week_options(),
            "current_year": datetime.now().year,
            "now": datetime.now()
        }
    )

@app.get("/reports/upload", response_class=HTMLResponse)
async def upload_report_page(request: Request):
    """Upload weekly report form (Open)"""
    conn = get_db_connection()
    facilities = get_all_facilities(conn)
    conn.close()
    
    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "facilities": facilities,
            "current_week": datetime.now().isocalendar()[1],
            "current_year": datetime.now().year,
            "sections": REPORT_SECTIONS,
            "now": datetime.now()
        }
    )

@app.post("/reports/upload")
async def upload_report(
    request: Request,
    facility_id: int = Form(...),
    week: int = Form(...),
    year: int = Form(...),
    report_file: UploadFile = File(None),
    report_text: str = Form(None)
):
    """Handle weekly report upload (Open)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if report already exists
    cursor.execute(
        "SELECT id FROM weekly_reports WHERE facility_id = ? AND week = ? AND year = ?",
        (facility_id, week, year)
    )
    existing = cursor.fetchone()
    
    if existing:
        facilities = get_all_facilities(conn)
        conn.close()
        return templates.TemplateResponse(
            "upload.html",
            {
                "request": request,
                "error": f"Report for Week {week}, {year} already exists",
                "facilities": facilities,
                "current_week": datetime.now().isocalendar()[1],
                "current_year": datetime.now().year,
                "sections": REPORT_SECTIONS,
                "now": datetime.now()
            }
        )
    
    try:
        if report_file:
            file_path = save_uploaded_file(report_file, Path(UPLOAD_DIR) / "public")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            report = parse_health_report(content, facility_id, week, year)
        elif report_text:
            report = parse_health_report(report_text, facility_id, week, year)
        else:
            raise ValueError("No report provided")
        
        validation_errors = validate_report_data(report)
        if validation_errors:
            facilities = get_all_facilities(conn)
            conn.close()
            return templates.TemplateResponse(
                "upload.html",
                {
                    "request": request,
                    "error": "Validation errors: " + ", ".join(validation_errors),
                    "facilities": facilities,
                    "current_week": datetime.now().isocalendar()[1],
                    "current_year": datetime.now().year,
                    "sections": REPORT_SECTIONS,
                    "now": datetime.now()
                }
            )
        
        report_id = save_weekly_report(conn, report)
        
        alerts = generate_alerts(conn, report)
        for alert in alerts:
            cursor.execute("""
                INSERT INTO alerts (facility_id, week, year, alert_type, severity, message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.get('facility_id'),
                alert.get('week'),
                alert.get('year'),
                alert.get('alert_type'),
                alert.get('severity'),
                alert.get('message'),
                datetime.now()
            ))
        conn.commit()
        
        facility = get_facility_by_id(conn, facility_id)
        reports = get_facility_reports(conn, facility_id, limit=12)
        generate_facility_dashboard(facility['name'], reports, Path(VISUALS_DIR) / f"facility_{facility_id}")
        
        conn.close()
        
        return RedirectResponse(
            url=f"/reports/{report_id}?success=Report uploaded successfully",
            status_code=302
        )
        
    except Exception as e:
        logger.error(f"Error processing report: {str(e)}")
        facilities = get_all_facilities(conn)
        conn.close()
        return templates.TemplateResponse(
            "upload.html",
            {
                "request": request,
                "error": f"Error processing report: {str(e)}",
                "facilities": facilities,
                "current_week": datetime.now().isocalendar()[1],
                "current_year": datetime.now().year,
                "sections": REPORT_SECTIONS,
                "now": datetime.now()
            }
        )

@app.get("/reports/{report_id}", response_class=HTMLResponse)
async def view_report(request: Request, report_id: int):
    """View a specific weekly report (Public)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT r.*, f.name as facility_name, f.type, f.district, f.province
        FROM weekly_reports r
        JOIN facilities f ON r.facility_id = f.id
        WHERE r.id = ?
    """, (report_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = dict(row)
    formatted_metrics = format_metrics_display(report)
    
    prev_week = report["week"] - 1 if report["week"] > 1 else 52
    prev_year = report["year"] if report["week"] > 1 else report["year"] - 1
    cursor.execute("""
        SELECT * FROM weekly_reports
        WHERE facility_id = ? AND week = ? AND year = ?
    """, (report["facility_id"], prev_week, prev_year))
    previous = cursor.fetchone()
    previous_dict = dict(previous) if previous else None
    
    conn.close()
    
    success_msg = request.query_params.get("success", "")
    return templates.TemplateResponse(
        "weekly_report.html",
        {
            "request": request,
            "report": report,
            "formatted_metrics": formatted_metrics,
            "previous_report": previous_dict,
            "success": success_msg,
            "sections": REPORT_SECTIONS,
            "current_year": datetime.now().year,
            "now": datetime.now()
        }
    )

@app.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request):
    """View all alerts (Public)"""
    conn = get_db_connection()
    alerts_data = get_alerts(conn)
    conn.close()
    
    alerts = [dict(a) for a in alerts_data] if alerts_data else []
    
    summary = {
        'total_unresolved': len([a for a in alerts if not a.get('resolved', False)]),
        'critical_unresolved': len([a for a in alerts if a.get('severity') == 'critical' and not a.get('resolved', False)]),
        'high_unresolved': len([a for a in alerts if a.get('severity') == 'high' and not a.get('resolved', False)]),
        'medium_unresolved': len([a for a in alerts if a.get('severity') == 'medium' and not a.get('resolved', False)]),
        'low_unresolved': len([a for a in alerts if a.get('severity') == 'low' and not a.get('resolved', False)]),
        'resolved': len([a for a in alerts if a.get('resolved', False)])
    }
    
    return templates.TemplateResponse(
        "alerts.html",
        {
            "request": request,
            "alerts": alerts,
            "summary": summary,
            "alert_thresholds": ALERT_THRESHOLDS,
            "current_year": datetime.now().year,
            "now": datetime.now()
        }
    )

@app.get("/export/facility/{facility_id}")
async def export_facility_data(request: Request, facility_id: int):
    """Export all data for a single facility (Public)"""
    conn = get_db_connection()
    reports = get_facility_reports(conn, facility_id, limit=1000)
    facility = get_facility_by_id(conn, facility_id)
    conn.close()
    
    df = pd.DataFrame(reports)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='All Reports', index=False)
        if not df.empty:
            summary = df.describe()
            summary.to_excel(writer, sheet_name='Summary')
    
    output.seek(0)
    filename = f"{facility['name'].replace(' ', '_')}_data_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ======================
# ERROR HANDLERS (Fixed with hardcoded URLs in templates)
# ======================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        "errors/404.html",
        {
            "request": request,
            "alert_count": 0,
            "current_year": datetime.now().year,
            "now": datetime.now()
        },
        status_code=404
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.error(f"Server error: {str(exc)}")
    return templates.TemplateResponse(
        "errors/500.html",
        {
            "request": request,
            "alert_count": 0,
            "current_year": datetime.now().year,
            "now": datetime.now()
        },
        status_code=500
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )