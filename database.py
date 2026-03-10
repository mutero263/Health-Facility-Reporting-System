"""
Database Layer for Health Facility Reporting System
SQLite-based storage for facilities, reports, users, and alerts
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from contextlib import contextmanager

from health_parser import HealthReport

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================
# CONFIGURATION
# ======================

DATABASE_PATH = Path("data/health_facility.db")

# ======================
# DATABASE INITIALIZATION
# ======================

def init_db(db_path: Path = DATABASE_PATH):
    """
    Initialize the database with all required tables
    
    Creates tables:
    - facilities: Health facility information
    - weekly_reports: Weekly report data
    - users: System users
    - alerts: System alerts and notifications
    - audit_log: Track data changes
    - targets: Performance targets by facility/district
    """
    logger.info(f"Initializing database at {db_path}")
    
    # Ensure data directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Create facilities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            district TEXT NOT NULL,
            province TEXT NOT NULL,
            catchment_population INTEGER DEFAULT 0,
            latitude REAL,
            longitude REAL,
            active BOOLEAN DEFAULT 1,
            opd_visits INTEGER DEFAULT 0,
            institutional_deliveries INTEGER DEFAULT 0,
            anc_contacts INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create weekly_reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER NOT NULL,
            week INTEGER NOT NULL,
            year INTEGER NOT NULL,
            report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- RDNS Metrics
            malaria_suspected TEXT DEFAULT '0/0',
            malaria_tested TEXT DEFAULT '0/0',
            malaria_positive TEXT DEFAULT '0/0',
            malaria_uncomplicated INTEGER DEFAULT 0,
            malaria_severe INTEGER DEFAULT 0,
            malaria_death INTEGER DEFAULT 0,
            malaria_history_travel TEXT DEFAULT 'No',
            diarrhoea TEXT DEFAULT '0/0',
            dysentery TEXT DEFAULT '0/0',
            suspected_dysentery TEXT DEFAULT '0/0',
            influenza TEXT DEFAULT '0/0',
            dog_bite INTEGER DEFAULT 0,
            kwashiorkor INTEGER DEFAULT 0,
            marasmus INTEGER DEFAULT 0,
            bilharzia INTEGER DEFAULT 0,
            maternal_death INTEGER DEFAULT 0,
            perinatal_death INTEGER DEFAULT 0,
            
            -- VHW Metrics
            vhw_malaria_suspected TEXT DEFAULT '0/0',
            vhw_malaria_tested TEXT DEFAULT '0/0',
            vhw_malaria_positive TEXT DEFAULT '0/0',
            vhw_diarrhoea TEXT DEFAULT '0/0',
            vhw_dysentery TEXT DEFAULT '0/0',
            
            -- AEFI Metrics
            aefi INTEGER DEFAULT 0,
            afp INTEGER DEFAULT 0,
            nnt INTEGER DEFAULT 0,
            measles INTEGER DEFAULT 0,
            
            -- OPD Metrics
            drs_resigned INTEGER DEFAULT 0,
            nurses_resigned INTEGER DEFAULT 0,
            casualty_visits INTEGER DEFAULT 0,
            opd_visits INTEGER DEFAULT 0,
            in_patients_admissions INTEGER DEFAULT 0,
            major_operations INTEGER DEFAULT 0,
            c_sections INTEGER DEFAULT 0,
            renal_dialysis INTEGER DEFAULT 0,
            
            -- Maternal Health
            anc_contacts INTEGER DEFAULT 0,
            fp_clients INTEGER DEFAULT 0,
            pnc_attendees INTEGER DEFAULT 0,
            institutional_deliveries INTEGER DEFAULT 0,
            home_deliveries INTEGER DEFAULT 0,
            still_births INTEGER DEFAULT 0,
            
            -- Child Health
            children_vaccinated_penta3 INTEGER DEFAULT 0,
            under5_sam INTEGER DEFAULT 0,
            under5_mam INTEGER DEFAULT 0,
            children_vitamin_a INTEGER DEFAULT 0,
            under5_deaths INTEGER DEFAULT 0,
            
            -- HIV/TB
            hiv_tested INTEGER DEFAULT 0,
            hiv_positive INTEGER DEFAULT 0,
            tb_new_relapse INTEGER DEFAULT 0,
            tb_screened INTEGER DEFAULT 0,
            
            -- Other
            institutional_deaths INTEGER DEFAULT 0,
            functional_ambulance INTEGER DEFAULT 0,
            xray_patients INTEGER DEFAULT 0,
            tracer_medicines_stock INTEGER DEFAULT 0,
            
            -- Metadata
            submitted_by INTEGER,
            data_quality_score REAL DEFAULT 100.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (facility_id) REFERENCES facilities (id),
            UNIQUE(facility_id, week, year)
        )
    """)
    
    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_facility ON weekly_reports(facility_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_date ON weekly_reports(year, week)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_facility_date ON weekly_reports(facility_id, year, week)")
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL,
            facility_id INTEGER,
            district TEXT,
            province TEXT,
            active BOOLEAN DEFAULT 1,
            api_key TEXT,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (facility_id) REFERENCES facilities (id)
        )
    """)
    
    # Create alerts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER NOT NULL,
            week INTEGER,
            year INTEGER,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            details TEXT,
            resolved BOOLEAN DEFAULT 0,
            resolved_by INTEGER,
            resolved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (facility_id) REFERENCES facilities (id),
            FOREIGN KEY (resolved_by) REFERENCES users (id)
        )
    """)
    
    # Create index for alerts
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_facility ON alerts(facility_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(resolved)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)")
    
    # Create audit_log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            table_name TEXT NOT NULL,
            record_id INTEGER,
            old_values TEXT,
            new_values TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Create targets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER,
            district TEXT,
            province TEXT,
            metric TEXT NOT NULL,
            target_value REAL NOT NULL,
            year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    
    logger.info("Database initialized successfully")


def get_db_connection(db_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    """Get a database connection with row factory enabled"""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_transaction(db_path: Path = DATABASE_PATH):
    """Context manager for database transactions"""
    conn = get_db_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction error: {str(e)}")
        raise
    finally:
        conn.close()


# ======================
# FACILITY OPERATIONS
# ======================

def create_facility(conn: sqlite3.Connection, facility: Dict[str, Any]) -> int:
    """Create a new facility record"""
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO facilities (
            name, type, district, province, catchment_population,
            latitude, longitude, active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        facility['name'],
        facility['type'],
        facility['district'],
        facility['province'],
        facility.get('catchment_population', 0),
        facility.get('latitude'),
        facility.get('longitude'),
        facility.get('active', 1),
        datetime.now(),
        datetime.now()
    ))
    
    facility_id = cursor.lastrowid
    
    # Log to audit
    log_audit(conn, None, 'CREATE', 'facilities', facility_id, None, facility)
    
    return facility_id


def get_facility_by_id(conn: sqlite3.Connection, facility_id: int) -> Optional[Dict[str, Any]]:
    """Get facility by ID"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM facilities WHERE id = ?", (facility_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_facility_by_name(conn: sqlite3.Connection, name: str, district: str = None) -> Optional[Dict[str, Any]]:
    """Get facility by name (and optionally district)"""
    cursor = conn.cursor()
    
    if district:
        cursor.execute("SELECT * FROM facilities WHERE name = ? AND district = ?", (name, district))
    else:
        cursor.execute("SELECT * FROM facilities WHERE name = ?", (name,))
    
    row = cursor.fetchone()
    return dict(row) if row else None


def get_all_facilities(conn: sqlite3.Connection, 
                       active_only: bool = True,
                       district: str = None,
                       province: str = None,
                       limit: int = None) -> List[Dict[str, Any]]:
    """Get all facilities with optional filters"""
    cursor = conn.cursor()
    
    query = "SELECT * FROM facilities WHERE 1=1"
    params = []
    
    if active_only:
        query += " AND active = 1"
    
    if district:
        query += " AND district = ?"
        params.append(district)
    
    if province:
        query += " AND province = ?"
        params.append(province)
    
    query += " ORDER BY name"
    
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def update_facility(conn: sqlite3.Connection, facility_id: int, updates: Dict[str, Any]) -> bool:
    """Update facility information"""
    cursor = conn.cursor()
    
    # Get old values for audit
    old = get_facility_by_id(conn, facility_id)
    if not old:
        return False
    
    # Build update query
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    updates['updated_at'] = datetime.now()
    
    query = f"UPDATE facilities SET {set_clause}, updated_at = ? WHERE id = ?"
    params = list(updates.values()) + [facility_id]
    
    cursor.execute(query, params)
    
    # Log to audit
    log_audit(conn, None, 'UPDATE', 'facilities', facility_id, old, updates)
    
    return cursor.rowcount > 0


def delete_facility(conn: sqlite3.Connection, facility_id: int, hard_delete: bool = False) -> bool:
    """Delete or deactivate a facility"""
    cursor = conn.cursor()
    
    if hard_delete:
        # Check for related records
        cursor.execute("SELECT COUNT(*) FROM weekly_reports WHERE facility_id = ?", (facility_id,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Soft delete instead
            return update_facility(conn, facility_id, {'active': 0})
        
        cursor.execute("DELETE FROM facilities WHERE id = ?", (facility_id,))
    else:
        cursor.execute("UPDATE facilities SET active = 0, updated_at = ? WHERE id = ?", 
                      (datetime.now(), facility_id))
    
    return cursor.rowcount > 0


def get_facility_districts(conn: sqlite3.Connection) -> List[str]:
    """Get list of distinct districts"""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT district FROM facilities WHERE active = 1 ORDER BY district")
    return [row['district'] for row in cursor.fetchall()]


def get_facility_provinces(conn: sqlite3.Connection) -> List[str]:
    """Get list of distinct provinces"""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT province FROM facilities WHERE active = 1 ORDER BY province")
    return [row['province'] for row in cursor.fetchall()]


# ======================
# REPORT OPERATIONS
# ======================

def save_weekly_report(conn: sqlite3.Connection, 
                       report: HealthReport,
                       user_id: int = None) -> int:
    """
    Save a weekly report to the database
    
    Args:
        conn: Database connection
        report: HealthReport object
        user_id: ID of user submitting the report
    
    Returns:
        ID of the inserted report
    """
    cursor = conn.cursor()
    
    # Check if report already exists
    cursor.execute("""
        SELECT id FROM weekly_reports 
        WHERE facility_id = ? AND week = ? AND year = ?
    """, (report.facility_id, report.week, report.year))
    
    existing = cursor.fetchone()
    
    if existing:
        # Update existing report
        report_id = existing['id']
        update_weekly_report(conn, report_id, report, user_id)
        return report_id
    
    # Convert report to dict for insertion
    data = report.__dict__.copy()
    
    # Remove non-column fields
    exclude_fields = ['facility_name', 'raw_text', 'additional_metrics']
    for field in exclude_fields:
        data.pop(field, None)
    
    # Build INSERT query
    columns = list(data.keys())
    placeholders = ','.join(['?'] * len(columns))
    
    query = f"""
        INSERT INTO weekly_reports ({', '.join(columns)})
        VALUES ({placeholders})
    """
    
    values = [data[col] for col in columns]
    
    cursor.execute(query, values)
    report_id = cursor.lastrowid
    
    # Log to audit
    log_audit(conn, user_id, 'CREATE', 'weekly_reports', report_id, None, data)
    
    logger.info(f"Saved weekly report ID {report_id} for facility {report.facility_id}, Week {report.week}")
    
    return report_id


def update_weekly_report(conn: sqlite3.Connection,
                         report_id: int,
                         report: HealthReport,
                         user_id: int = None) -> bool:
    """Update an existing weekly report"""
    cursor = conn.cursor()
    
    # Get old values
    cursor.execute("SELECT * FROM weekly_reports WHERE id = ?", (report_id,))
    old = cursor.fetchone()
    if not old:
        return False
    
    old_dict = dict(old)
    
    # Convert report to dict for update
    data = report.__dict__.copy()
    
    # Remove non-column fields
    exclude_fields = ['facility_name', 'raw_text', 'additional_metrics']
    for field in exclude_fields:
        data.pop(field, None)
    
    # Add updated timestamp
    data['updated_at'] = datetime.now()
    
    # Build UPDATE query
    set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
    
    query = f"UPDATE weekly_reports SET {set_clause} WHERE id = ?"
    values = list(data.values()) + [report_id]
    
    cursor.execute(query, values)
    
    # Log to audit
    log_audit(conn, user_id, 'UPDATE', 'weekly_reports', report_id, old_dict, data)
    
    return cursor.rowcount > 0


def get_weekly_report(conn: sqlite3.Connection, 
                      facility_id: int, 
                      week: int, 
                      year: int) -> Optional[Dict[str, Any]]:
    """Get a specific weekly report"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, f.name as facility_name, f.district, f.province
        FROM weekly_reports r
        JOIN facilities f ON r.facility_id = f.id
        WHERE r.facility_id = ? AND r.week = ? AND r.year = ?
    """, (facility_id, week, year))
    
    row = cursor.fetchone()
    return dict(row) if row else None


def get_report_by_id(conn: sqlite3.Connection, report_id: int) -> Optional[Dict[str, Any]]:
    """Get report by ID with facility info"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, f.name as facility_name, f.district, f.province, f.type
        FROM weekly_reports r
        JOIN facilities f ON r.facility_id = f.id
        WHERE r.id = ?
    """, (report_id,))
    
    row = cursor.fetchone()
    return dict(row) if row else None


def get_facility_reports(conn: sqlite3.Connection,
                         facility_id: int,
                         start_week: int = None,
                         end_week: int = None,
                         start_year: int = None,
                         end_year: int = None,
                         limit: int = None,
                         sort_desc: bool = True) -> List[Dict[str, Any]]:
    """Get reports for a specific facility with optional date range"""
    cursor = conn.cursor()
    
    query = "SELECT * FROM weekly_reports WHERE facility_id = ?"
    params = [facility_id]
    
    if start_week and start_year:
        query += " AND (year > ? OR (year = ? AND week >= ?))"
        params.extend([start_year, start_year, start_week])
    
    if end_week and end_year:
        query += " AND (year < ? OR (year = ? AND week <= ?))"
        params.extend([end_year, end_year, end_week])
    
    query += " ORDER BY year " + ("DESC" if sort_desc else "ASC") + ", week " + ("DESC" if sort_desc else "ASC")
    
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def get_reports_by_date_range(conn: sqlite3.Connection,
                              start_week: int,
                              start_year: int,
                              end_week: int,
                              end_year: int,
                              facility_ids: List[int] = None,
                              district: str = None) -> List[Dict[str, Any]]:
    """Get reports across facilities for a date range"""
    cursor = conn.cursor()
    
    query = """
        SELECT r.*, f.name as facility_name, f.district, f.province
        FROM weekly_reports r
        JOIN facilities f ON r.facility_id = f.id
        WHERE (r.year > ? OR (r.year = ? AND r.week >= ?))
          AND (r.year < ? OR (r.year = ? AND r.week <= ?))
    """
    
    params = [start_year, start_year, start_week, end_year, end_year, end_week]
    
    if facility_ids:
        placeholders = ','.join(['?'] * len(facility_ids))
        query += f" AND r.facility_id IN ({placeholders})"
        params.extend(facility_ids)
    
    if district:
        query += " AND f.district = ?"
        params.append(district)
    
    query += " ORDER BY f.name, r.year, r.week"
    
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def delete_weekly_report(conn: sqlite3.Connection, report_id: int, user_id: int = None) -> bool:
    """Delete a weekly report"""
    cursor = conn.cursor()
    
    # Get report for audit
    cursor.execute("SELECT * FROM weekly_reports WHERE id = ?", (report_id,))
    report = cursor.fetchone()
    
    if not report:
        return False
    
    cursor.execute("DELETE FROM weekly_reports WHERE id = ?", (report_id,))
    
    # Log to audit
    log_audit(conn, user_id, 'DELETE', 'weekly_reports', report_id, dict(report), None)
    
    return cursor.rowcount > 0


def get_latest_report_week(conn: sqlite3.Connection, facility_id: int = None) -> Tuple[int, int]:
    """Get the latest week/year with reports"""
    cursor = conn.cursor()
    
    if facility_id:
        cursor.execute("""
            SELECT year, week FROM weekly_reports 
            WHERE facility_id = ? 
            ORDER BY year DESC, week DESC LIMIT 1
        """, (facility_id,))
    else:
        cursor.execute("""
            SELECT year, week FROM weekly_reports 
            ORDER BY year DESC, week DESC LIMIT 1
        """)
    
    row = cursor.fetchone()
    if row:
        return row['year'], row['week']
    return datetime.now().year, 1


# ======================
# REPORT AGGREGATION
# ======================

def get_weekly_summary(conn: sqlite3.Connection,
                       week: int = None,
                       year: int = None,
                       district: str = None) -> Dict[str, Any]:
    """Get summary statistics for a specific week"""
    cursor = conn.cursor()
    
    if not week or not year:
        year, week = get_latest_report_week(conn)
    
    query = """
        SELECT 
            COUNT(DISTINCT r.facility_id) as facilities_reporting,
            SUM(r.opd_visits) as total_opd,
            SUM(r.institutional_deliveries) as total_deliveries,
            SUM(r.anc_contacts) as total_anc,
            SUM(r.fp_clients) as total_fp,
            SUM(r.pnc_attendees) as total_pnc,
            SUM(r.hiv_tested) as total_hiv_tested,
            SUM(r.children_vaccinated_penta3) as total_vaccinated,
            SUM(r.tb_screened) as total_tb_screened,
            AVG(r.opd_visits) as avg_opd,
            SUM(CASE WHEN r.malaria_positive != '0/0' 
                THEN CAST(SUBSTR(r.malaria_positive, 1, INSTR(r.malaria_positive, '/')-1) AS INTEGER)
                ELSE 0 END) as total_malaria_positive
        FROM weekly_reports r
        JOIN facilities f ON r.facility_id = f.id
        WHERE r.week = ? AND r.year = ?
    """
    
    params = [week, year]
    
    if district:
        query += " AND f.district = ?"
        params.append(district)
    
    cursor.execute(query, params)
    summary = dict(cursor.fetchone())
    
    # Get total facilities in district/area
    facility_query = "SELECT COUNT(*) as total FROM facilities WHERE active = 1"
    if district:
        facility_query += " AND district = ?"
        cursor.execute(facility_query, (district,))
    else:
        cursor.execute(facility_query)
    
    total_facilities = cursor.fetchone()['total']
    
    summary['total_facilities'] = total_facilities
    summary['reporting_rate'] = (summary['facilities_reporting'] / total_facilities * 100) if total_facilities > 0 else 0
    summary['week'] = week
    summary['year'] = year
    
    return summary


def get_facility_aggregates(conn: sqlite3.Connection,
                            facility_id: int,
                            start_week: int = None,
                            end_week: int = None,
                            start_year: int = None,
                            end_year: int = None) -> Dict[str, Any]:
    """Get aggregate statistics for a facility over a period"""
    cursor = conn.cursor()
    
    query = """
        SELECT 
            COUNT(*) as weeks_reported,
            SUM(opd_visits) as total_opd,
            AVG(opd_visits) as avg_weekly_opd,
            SUM(institutional_deliveries) as total_deliveries,
            SUM(anc_contacts) as total_anc,
            SUM(fp_clients) as total_fp,
            SUM(pnc_attendees) as total_pnc,
            SUM(hiv_tested) as total_hiv_tested,
            SUM(children_vaccinated_penta3) as total_vaccinated,
            SUM(tb_screened) as total_tb_screened,
            SUM(CASE WHEN malaria_positive != '0/0' 
                THEN CAST(SUBSTR(malaria_positive, 1, INSTR(malaria_positive, '/')-1) AS INTEGER)
                ELSE 0 END) as total_malaria_positive,
            SUM(CASE WHEN malaria_tested != '0/0' 
                THEN CAST(SUBSTR(malaria_tested, 1, INSTR(malaria_tested, '/')-1) AS INTEGER)
                ELSE 0 END) as total_malaria_tested,
            MIN(report_date) as first_report,
            MAX(report_date) as last_report
        FROM weekly_reports
        WHERE facility_id = ?
    """
    
    params = [facility_id]
    
    if start_week and start_year:
        query += " AND (year > ? OR (year = ? AND week >= ?))"
        params.extend([start_year, start_year, start_week])
    
    if end_week and end_year:
        query += " AND (year < ? OR (year = ? AND week <= ?))"
        params.extend([end_year, end_year, end_week])
    
    cursor.execute(query, params)
    aggregates = dict(cursor.fetchone())
    
    # Calculate derived metrics
    if aggregates['total_malaria_tested'] > 0:
        aggregates['malaria_positivity_rate'] = aggregates['total_malaria_positive'] / aggregates['total_malaria_tested']
    else:
        aggregates['malaria_positivity_rate'] = 0
    
    return aggregates


def get_district_aggregates(conn: sqlite3.Connection,
                            district: str,
                            week: int = None,
                            year: int = None) -> Dict[str, Any]:
    """Get aggregate statistics for a district"""
    cursor = conn.cursor()
    
    if not week or not year:
        year, week = get_latest_report_week(conn)
    
    query = """
        SELECT 
            COUNT(DISTINCT r.facility_id) as facilities_reporting,
            COUNT(DISTINCT f.id) as total_facilities,
            SUM(r.opd_visits) as total_opd,
            SUM(r.institutional_deliveries) as total_deliveries,
            SUM(r.anc_contacts) as total_anc,
            SUM(r.fp_clients) as total_fp,
            SUM(r.hiv_tested) as total_hiv_tested,
            SUM(r.children_vaccinated_penta3) as total_vaccinated,
            AVG(r.opd_visits) as avg_opd
        FROM facilities f
        LEFT JOIN weekly_reports r ON f.id = r.facility_id AND r.week = ? AND r.year = ?
        WHERE f.district = ? AND f.active = 1
    """
    
    cursor.execute(query, (week, year, district))
    aggregates = dict(cursor.fetchone())
    
    aggregates['week'] = week
    aggregates['year'] = year
    aggregates['district'] = district
    aggregates['reporting_rate'] = (aggregates['facilities_reporting'] / aggregates['total_facilities'] * 100) if aggregates['total_facilities'] > 0 else 0
    
    return aggregates


# ======================
# ALERT OPERATIONS
# ======================

def create_alert(conn: sqlite3.Connection,
                 facility_id: int,
                 alert_type: str,
                 severity: str,
                 message: str,
                 week: int = None,
                 year: int = None,
                 details: Dict = None) -> int:
    """Create a new alert"""
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO alerts (facility_id, week, year, alert_type, severity, message, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        facility_id,
        week,
        year,
        alert_type,
        severity,
        message,
        json.dumps(details) if details else None,
        datetime.now()
    ))
    
    return cursor.lastrowid


def get_alerts(conn: sqlite3.Connection,
               facility_id: int = None,
               district: str = None,
               severity: str = None,
               alert_type: str = None,
               resolved: bool = False,
               limit: int = 100) -> List[Dict[str, Any]]:
    """Get alerts with optional filters"""
    cursor = conn.cursor()
    
    query = """
        SELECT a.*, f.name as facility_name, f.district
        FROM alerts a
        JOIN facilities f ON a.facility_id = f.id
        WHERE 1=1
    """
    params = []
    
    if facility_id:
        query += " AND a.facility_id = ?"
        params.append(facility_id)
    
    if district:
        query += " AND f.district = ?"
        params.append(district)
    
    if severity:
        query += " AND a.severity = ?"
        params.append(severity)
    
    if alert_type:
        query += " AND a.alert_type = ?"
        params.append(alert_type)
    
    query += " AND a.resolved = ?"
    params.append(1 if resolved else 0)
    
    query += " ORDER BY a.created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    
    alerts = []
    for row in cursor.fetchall():
        alert = dict(row)
        if alert['details']:
            try:
                alert['details'] = json.loads(alert['details'])
            except:
                pass
        alerts.append(alert)
    
    return alerts


def resolve_alert(conn: sqlite3.Connection, alert_id: int, resolved_by: int = None) -> bool:
    """Mark an alert as resolved"""
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE alerts 
        SET resolved = 1, resolved_by = ?, resolved_at = ?
        WHERE id = ?
    """, (resolved_by, datetime.now(), alert_id))
    
    return cursor.rowcount > 0


def get_alert_summary(conn: sqlite3.Connection, district: str = None) -> Dict[str, Any]:
    """Get summary of alerts"""
    cursor = conn.cursor()
    
    query = """
        SELECT 
            COUNT(*) as total_alerts,
            SUM(CASE WHEN severity = 'critical' AND resolved = 0 THEN 1 ELSE 0 END) as critical_unresolved,
            SUM(CASE WHEN severity = 'high' AND resolved = 0 THEN 1 ELSE 0 END) as high_unresolved,
            SUM(CASE WHEN severity = 'medium' AND resolved = 0 THEN 1 ELSE 0 END) as medium_unresolved,
            SUM(CASE WHEN severity = 'low' AND resolved = 0 THEN 1 ELSE 0 END) as low_unresolved,
            COUNT(DISTINCT facility_id) as facilities_with_alerts
        FROM alerts a
        JOIN facilities f ON a.facility_id = f.id
        WHERE 1=1
    """
    
    params = []
    if district:
        query += " AND f.district = ?"
        params.append(district)
    
    cursor.execute(query, params)
    return dict(cursor.fetchone())


# ======================
# USER OPERATIONS
# ======================

def create_user(conn: sqlite3.Connection, user: Dict[str, Any]) -> int:
    """Create a new user"""
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO users (
            username, password_hash, full_name, email, role,
            facility_id, district, province, active, api_key, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user['username'],
        user['password_hash'],
        user['full_name'],
        user.get('email'),
        user['role'],
        user.get('facility_id'),
        user.get('district'),
        user.get('province'),
        user.get('active', 1),
        user.get('api_key'),
        datetime.now(),
        datetime.now()
    ))
    
    return cursor.lastrowid


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_user_by_username(conn: sqlite3.Connection, username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_users(conn: sqlite3.Connection,
              role: str = None,
              facility_id: int = None,
              active_only: bool = True) -> List[Dict[str, Any]]:
    """Get users with optional filters"""
    cursor = conn.cursor()
    
    query = "SELECT * FROM users WHERE 1=1"
    params = []
    
    if role:
        query += " AND role = ?"
        params.append(role)
    
    if facility_id:
        query += " AND facility_id = ?"
        params.append(facility_id)
    
    if active_only:
        query += " AND active = 1"
    
    query += " ORDER BY username"
    
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def update_user(conn: sqlite3.Connection, user_id: int, updates: Dict[str, Any]) -> bool:
    """Update user information"""
    cursor = conn.cursor()
    
    updates['updated_at'] = datetime.now()
    
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    query = f"UPDATE users SET {set_clause} WHERE id = ?"
    params = list(updates.values()) + [user_id]
    
    cursor.execute(query, params)
    return cursor.rowcount > 0


def update_last_login(conn: sqlite3.Connection, user_id: int) -> bool:
    """Update user's last login timestamp"""
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now(), user_id))
    return cursor.rowcount > 0


def delete_user(conn: sqlite3.Connection, user_id: int, hard_delete: bool = False) -> bool:
    """Delete or deactivate a user"""
    if hard_delete:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0
    else:
        return update_user(conn, user_id, {'active': 0})


# ======================
# AUDIT LOG
# ======================

def log_audit(conn: sqlite3.Connection,
              user_id: int,
              action: str,
              table_name: str,
              record_id: int,
              old_values: Dict = None,
              new_values: Dict = None,
              ip_address: str = None):
    """Log an audit entry"""
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO audit_log (user_id, action, table_name, record_id, old_values, new_values, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        action,
        table_name,
        record_id,
        json.dumps(old_values) if old_values else None,
        json.dumps(new_values) if new_values else None,
        ip_address
    ))
    
    conn.commit()


def get_audit_log(conn: sqlite3.Connection,
                  user_id: int = None,
                  table_name: str = None,
                  limit: int = 100) -> List[Dict[str, Any]]:
    """Get audit log entries"""
    cursor = conn.cursor()
    
    query = "SELECT * FROM audit_log WHERE 1=1"
    params = []
    
    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)
    
    if table_name:
        query += " AND table_name = ?"
        params.append(table_name)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    
    logs = []
    for row in cursor.fetchall():
        log = dict(row)
        if log['old_values']:
            try:
                log['old_values'] = json.loads(log['old_values'])
            except:
                pass
        if log['new_values']:
            try:
                log['new_values'] = json.loads(log['new_values'])
            except:
                pass
        logs.append(log)
    
    return logs


# ======================
# TARGET OPERATIONS
# ======================

def create_target(conn: sqlite3.Connection, target: Dict[str, Any]) -> int:
    """Create a new target"""
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO targets (facility_id, district, province, metric, target_value, year, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        target.get('facility_id'),
        target.get('district'),
        target.get('province'),
        target['metric'],
        target['target_value'],
        target.get('year'),
        datetime.now(),
        datetime.now()
    ))
    
    return cursor.lastrowid


def get_targets(conn: sqlite3.Connection,
                facility_id: int = None,
                district: str = None,
                province: str = None,
                metric: str = None,
                year: int = None) -> List[Dict[str, Any]]:
    """Get targets with optional filters"""
    cursor = conn.cursor()
    
    query = "SELECT * FROM targets WHERE 1=1"
    params = []
    
    if facility_id:
        query += " AND facility_id = ?"
        params.append(facility_id)
    
    if district:
        query += " AND district = ?"
        params.append(district)
    
    if province:
        query += " AND province = ?"
        params.append(province)
    
    if metric:
        query += " AND metric = ?"
        params.append(metric)
    
    if year:
        query += " AND year = ?"
        params.append(year)
    
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def update_target(conn: sqlite3.Connection, target_id: int, updates: Dict[str, Any]) -> bool:
    """Update a target"""
    cursor = conn.cursor()
    
    updates['updated_at'] = datetime.now()
    
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    query = f"UPDATE targets SET {set_clause} WHERE id = ?"
    params = list(updates.values()) + [target_id]
    
    cursor.execute(query, params)
    return cursor.rowcount > 0


def delete_target(conn: sqlite3.Connection, target_id: int) -> bool:
    """Delete a target"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM targets WHERE id = ?", (target_id,))
    return cursor.rowcount > 0


# ======================
# SETTINGS OPERATIONS
# ======================

def get_setting(conn: sqlite3.Connection, key: str, default: Any = None) -> Any:
    """Get a setting value"""
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    
    if row:
        try:
            return json.loads(row['value'])
        except:
            return row['value']
    
    return default


def set_setting(conn: sqlite3.Connection, key: str, value: Any, description: str = None):
    """Set a setting value"""
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM settings WHERE key = ?", (key,))
    exists = cursor.fetchone()
    
    value_json = json.dumps(value) if not isinstance(value, str) else value
    
    if exists:
        cursor.execute("""
            UPDATE settings SET value = ?, description = ?, updated_at = ? WHERE key = ?
        """, (value_json, description, datetime.now(), key))
    else:
        cursor.execute("""
            INSERT INTO settings (key, value, description, updated_at) VALUES (?, ?, ?, ?)
        """, (key, value_json, description, datetime.now()))
    
    conn.commit()


# ======================
# CLEANUP FUNCTIONS
# ======================

def cleanup_old_alerts(conn: sqlite3.Connection, days: int = 30):
    """Delete alerts older than specified days"""
    cursor = conn.cursor()
    cutoff = datetime.now() - timedelta(days=days)
    
    cursor.execute("DELETE FROM alerts WHERE created_at < ?", (cutoff,))
    deleted = cursor.rowcount
    conn.commit()
    
    logger.info(f"Deleted {deleted} old alerts")
    return deleted


def cleanup_old_audit_logs(conn: sqlite3.Connection, days: int = 90):
    """Delete audit logs older than specified days"""
    cursor = conn.cursor()
    cutoff = datetime.now() - timedelta(days=days)
    
    cursor.execute("DELETE FROM audit_log WHERE created_at < ?", (cutoff,))
    deleted = cursor.rowcount
    conn.commit()
    
    logger.info(f"Deleted {deleted} old audit logs")
    return deleted


# ======================
# EXPORTS
# ======================

__all__ = [
    # Database initialization
    'init_db',
    'get_db_connection',
    'db_transaction',
    
    # Facility operations
    'create_facility',
    'get_facility_by_id',
    'get_facility_by_name',
    'get_all_facilities',
    'update_facility',
    'delete_facility',
    'get_facility_districts',
    'get_facility_provinces',
    
    # Report operations
    'save_weekly_report',
    'update_weekly_report',
    'get_weekly_report',
    'get_report_by_id',
    'get_facility_reports',
    'get_reports_by_date_range',
    'delete_weekly_report',
    'get_latest_report_week',
    
    # Aggregation
    'get_weekly_summary',
    'get_facility_aggregates',
    'get_district_aggregates',
    
    # Alert operations
    'create_alert',
    'get_alerts',
    'resolve_alert',
    'get_alert_summary',
    
    # User operations
    'create_user',
    'get_user_by_id',
    'get_user_by_username',
    'get_users',
    'update_user',
    'update_last_login',
    'delete_user',
    
    # Audit log
    'log_audit',
    'get_audit_log',
    
    # Target operations
    'create_target',
    'get_targets',
    'update_target',
    'delete_target',
    
    # Settings
    'get_setting',
    'set_setting',
    
    # Cleanup
    'cleanup_old_alerts',
    'cleanup_old_audit_logs'
]


# ======================
# MAIN TEST FUNCTION
# ======================

if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Test connection
    conn = get_db_connection()
    print("Database initialized successfully")
    
    # Test facility creation
    test_facility = {
        'name': 'Test Clinic',
        'type': 'clinic',
        'district': 'Test District',
        'province': 'Test Province',
        'catchment_population': 5000,
        'active': True
    }
    
    facility_id = create_facility(conn, test_facility)
    print(f"Created test facility with ID: {facility_id}")
    
    # Test getting facilities
    facilities = get_all_facilities(conn)
    print(f"Total facilities: {len(facilities)}")
    
    conn.close()
    print("Database test complete")