"""
Configuration Settings for Health Facility Reporting System
Centralized configuration management
"""

import os
from pathlib import Path
from datetime import timedelta
from typing import Dict, List, Any, Optional
import json
import logging

# ======================
# BASE PATHS
# ======================

# Base directory of the application
BASE_DIR = Path(__file__).parent.absolute()

# Data directories
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
EXPORTS_DIR = BASE_DIR / "exports"
LOGS_DIR = BASE_DIR / "logs"
VISUALS_DIR = BASE_DIR / "visuals"
# Create directories if they don't exist
for directory in [DATA_DIR, UPLOAD_DIR, STATIC_DIR, TEMPLATES_DIR, EXPORTS_DIR, LOGS_DIR, VISUALS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database path
DATABASE_PATH = DATA_DIR / "health_facility.db"

# ======================
# APPLICATION SETTINGS
# ======================

APP_NAME = "Health Facility Reporting System"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "System for tracking and analyzing health facility weekly reports"
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
TESTING = False

# Server settings
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8002))
WORKERS = int(os.environ.get("WORKERS", 4))

# Security
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SESSION_MAX_AGE = 24 * 60 * 60  # 24 hours in seconds

# CORS
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# Rate limiting
RATE_LIMIT_ENABLED = True
RATE_LIMIT_REQUESTS = 100  # requests per window
RATE_LIMIT_WINDOW = 60  # seconds

# ======================
# FILE UPLOAD SETTINGS
# ======================

# Maximum file size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    '.txt', '.csv', '.xlsx', '.xls', '.json', '.pdf'
}

# Upload settings
UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1 MB chunks
MAX_FILENAME_LENGTH = 255
CLEANUP_DAYS = 7  # Delete uploads older than this

# ======================
# FACILITY TYPES
# ======================

FACILITY_TYPES = [
    {"id": "hospital", "name": "Hospital", "level": 1},
    {"id": "rhc", "name": "Rural Health Centre", "level": 2},
    {"id": "clinic", "name": "Clinic", "level": 3},
    {"id": "uhc", "name": "Urban Health Centre", "level": 2},
    {"id": "dispensary", "name": "Dispensary", "level": 3},
    {"id": "health_post", "name": "Health Post", "level": 4},
]

FACILITY_TYPE_CHOICES = [t["id"] for t in FACILITY_TYPES]

# ======================
# USER ROLES
# ======================

USER_ROLES = [
    {"id": "admin", "name": "System Administrator", "level": 100},
    {"id": "district_manager", "name": "District Health Manager", "level": 80},
    {"id": "provincial_manager", "name": "Provincial Health Manager", "level": 90},
    {"id": "facility_manager", "name": "Facility Manager", "level": 60},
    {"id": "data_entry", "name": "Data Entry Clerk", "level": 40},
    {"id": "public_health_officer", "name": "Public Health Officer", "level": 70},
    {"id": "viewer", "name": "Viewer (Read Only)", "level": 20},
]

USER_ROLE_CHOICES = [r["id"] for r in USER_ROLES]

# Role permissions mapping
ROLE_PERMISSIONS = {
    "admin": ["*"],  # All permissions
    "district_manager": [
        "view_facilities", "view_reports", "create_alerts", 
        "export_data", "manage_district_users", "view_analytics"
    ],
    "provincial_manager": [
        "view_facilities", "view_reports", "view_analytics", "export_data"
    ],
    "facility_manager": [
        "view_own_facility", "create_reports", "edit_own_reports",
        "view_own_alerts", "export_own_data"
    ],
    "data_entry": [
        "view_own_facility", "create_reports", "edit_own_reports"
    ],
    "public_health_officer": [
        "view_facilities", "view_reports", "view_analytics", "view_alerts"
    ],
    "viewer": [
        "view_facilities", "view_reports"
    ],
}

# ======================
# REPORT SECTIONS
# ======================

REPORT_SECTIONS = [
    {
        "id": "rdns",
        "name": "RDNS (Routine Data)",
        "description": "Routine Disease Notification System data",
        "icon": "fa-chart-line",
        "fields": [
            "malaria_suspected", "malaria_tested", "malaria_positive",
            "malaria_uncomplicated", "malaria_death", "malaria_history_travel",
            "diarrhoea", "dysentery", "suspected_dysentery", "influenza",
            "dog_bite", "kwashiorkor", "marasmus", "bilharzia",
            "maternal_death", "perinatal_death"
        ]
    },
    {
        "id": "vhw",
        "name": "VHW (Village Health Workers)",
        "description": "Community-level health data",
        "icon": "fa-users",
        "fields": [
            "vhw_malaria_suspected", "vhw_malaria_tested", "vhw_malaria_positive",
            "vhw_diarrhoea", "vhw_dysentery"
        ]
    },
    {
        "id": "aefi",
        "name": "AEFI & Surveillance",
        "description": "Adverse events and disease surveillance",
        "icon": "fa-exclamation-triangle",
        "fields": [
            "aefi", "afp", "nnt", "measles"
        ]
    },
    {
        "id": "opd",
        "name": "OPD & Services",
        "description": "Outpatient department and clinical services",
        "icon": "fa-hospital",
        "fields": [
            "drs_resigned", "nurses_resigned", "casualty_visits",
            "opd_visits", "in_patients_admissions", "major_operations",
            "c_sections", "renal_dialysis"
        ]
    },
    {
        "id": "maternal",
        "name": "Maternal Health",
        "description": "Maternal and reproductive health services",
        "icon": "fa-female",
        "fields": [
            "anc_contacts", "fp_clients", "pnc_attendees",
            "institutional_deliveries", "home_deliveries", "still_births"
        ]
    },
    {
        "id": "child",
        "name": "Child Health",
        "description": "Child health and nutrition",
        "icon": "fa-child",
        "fields": [
            "children_vaccinated_penta3", "under5_sam", "under5_mam",
            "children_vitamin_a", "under5_deaths"
        ]
    },
    {
        "id": "hiv_tb",
        "name": "HIV & TB",
        "description": "HIV testing and TB screening",
        "icon": "fa-heartbeat",
        "fields": [
            "hiv_tested", "hiv_positive", "tb_new_relapse", "tb_screened"
        ]
    },
    {
        "id": "other",
        "name": "Other Indicators",
        "description": "Other facility indicators",
        "icon": "fa-ellipsis-h",
        "fields": [
            "institutional_deaths", "functional_ambulance",
            "xray_patients", "tracer_medicines_stock"
        ]
    }
]

# ======================
# ALERT THRESHOLDS
# ======================

ALERT_THRESHOLDS = {
    "malaria_positivity_rate": {
        "warning": 0.10,  # 10% positivity rate triggers warning
        "critical": 0.20,  # 20% positivity rate triggers critical alert
        "description": "Malaria positivity rate threshold"
    },
    "opd_visits": {
        "zero_weeks": 2,  # 2 weeks of zero OPD visits triggers alert
        "sudden_drop": 0.5,  # 50% drop from average
        "description": "OPD volume alerts"
    },
    "institutional_deliveries": {
        "zero_weeks": 4,  # 4 weeks with no deliveries
        "description": "Zero delivery weeks"
    },
    "home_deliveries": {
        "high_rate": 0.3,  # 30% home deliveries is concerning
        "description": "High home delivery rate"
    },
    "maternal_health": {
        "zero_deliveries_weeks": 4,
        "low_anc_ratio": 2.0,  # Less than 2 ANC per delivery
        "description": "Maternal health alerts"
    },
    "vaccination": {
        "zero_penta_weeks": 3,  # 3 weeks with no pentavalent vaccinations
        "description": "Zero vaccination weeks"
    },
    "hiv_testing": {
        "zero_testing_weeks": 4,  # 4 weeks with no HIV tests
        "low_testing_rate": 0.05,  # Less than 5% of OPD tested
        "description": "HIV testing alerts"
    },
    "tb_screening": {
        "low_screening": 10,  # Less than 10 TB screens per week
        "description": "Low TB screening"
    },
    "data_quality": {
        "missing_rdns": True,
        "inconsistent_data": True,
        "max_zero_metrics": 5,  # Maximum number of zero metrics before alert
        "description": "Data quality alerts"
    },
    "stock": {
        "tracer_medicines_zero": 2,  # Weeks with zero tracer medicines
        "description": "Stock availability alerts"
    }
}

# ======================
# PERFORMANCE TARGETS
# ======================

DEFAULT_TARGETS = {
    "institutional_delivery_rate": {
        "target": 0.90,  # 90% of deliveries in facility
        "description": "Institutional delivery rate target"
    },
    "anc_coverage": {
        "target": 0.85,  # 85% of expected pregnancies
        "description": "ANC coverage target"
    },
    "pnc_coverage": {
        "target": 0.80,  # 80% postnatal follow-up
        "description": "PNC coverage target"
    },
    "penta3_coverage": {
        "target": 0.95,  # 95% vaccination coverage
        "description": "Penta3 vaccination coverage"
    },
    "malaria_testing_rate": {
        "target": 0.95,  # 95% of suspected cases tested
        "description": "Malaria testing rate"
    },
    "hiv_testing_yield": {
        "target": 0.05,  # 5% positivity rate expected
        "description": "HIV testing yield"
    },
    "tb_screening_rate": {
        "target": 0.20,  # 20% of OPD screened for TB
        "description": "TB screening rate"
    },
    "fp_acceptance_rate": {
        "target": 0.30,  # 30% of eligible women
        "description": "Family planning acceptance"
    }
}

# ======================
# PERFORMANCE INDICATORS
# ======================

PERFORMANCE_INDICATORS = {
    "malaria_management": {
        "name": "Malaria Management",
        "indicators": [
            "malaria_testing_rate",
            "malaria_positivity_rate",
            "malaria_treatment_rate"
        ],
        "weight": 20
    },
    "maternal_health": {
        "name": "Maternal Health",
        "indicators": [
            "institutional_delivery_rate",
            "anc_coverage",
            "pnc_coverage",
            "fp_acceptance_rate"
        ],
        "weight": 30
    },
    "child_health": {
        "name": "Child Health",
        "indicators": [
            "penta3_coverage",
            "vitamin_a_coverage",
            "sam_treatment_rate"
        ],
        "weight": 20
    },
    "hiv_tb": {
        "name": "HIV & TB",
        "indicators": [
            "hiv_testing_rate",
            "hiv_positivity_rate",
            "tb_screening_rate",
            "tb_case_detection"
        ],
        "weight": 15
    },
    "service_volume": {
        "name": "Service Volume",
        "indicators": [
            "opd_per_capita",
            "admission_rate",
            "major_surgery_rate"
        ],
        "weight": 15
    }
}

# ======================
# DATA QUALITY RULES
# ======================

DATA_QUALITY_RULES = {
    "required_fields": [
        "facility_id", "week", "year", "opd_visits",
        "malaria_suspected", "malaria_tested", "malaria_positive"
    ],
    "consistency_rules": [
        {
            "name": "tested_less_than_suspected",
            "condition": "malaria_tested_numerator <= malaria_suspected_numerator",
            "message": "Malaria tested exceeds suspected cases"
        },
        {
            "name": "positive_less_than_tested",
            "condition": "malaria_positive_numerator <= malaria_tested_numerator",
            "message": "Malaria positive exceeds tested"
        },
        {
            "name": "still_births_less_than_deliveries",
            "condition": "still_births <= institutional_deliveries",
            "message": "Still births exceed deliveries"
        }
    ],
    "range_rules": [
        {
            "name": "week_range",
            "field": "week",
            "min": 1,
            "max": 53,
            "message": "Week must be between 1 and 53"
        },
        {
            "name": "year_range",
            "field": "year",
            "min": 2000,
            "max": 2100,
            "message": "Year must be between 2000 and 2100"
        }
    ]
}

# ======================
# VISUALIZATION SETTINGS
# ======================

VISUALIZATION_CONFIG = {
    "figure_sizes": {
        "small": (8, 4),
        "medium": (12, 6),
        "large": (16, 8),
        "dashboard": (20, 24)
    },
    "colors": {
        "primary": "#2E86AB",
        "secondary": "#A23B72",
        "success": "#28A745",
        "warning": "#FFC107",
        "danger": "#DC3545",
        "info": "#17A2B8",
        "light": "#F8F9FA",
        "dark": "#343A40",
        "maternal": "#A23B72",
        "child": "#28A745",
        "malaria": "#DC3545",
        "hiv": "#FFC107",
        "tb": "#17A2B8"
    },
    "dpi": 100,
    "default_style": "seaborn-v0_8-darkgrid",
    "export_formats": ["png", "jpg", "pdf", "svg"]
}

# ======================
# EXPORT SETTINGS
# ======================

EXPORT_CONFIG = {
    "excel": {
        "enabled": True,
        "max_rows": 100000,
        "sheet_name_limit": 31
    },
    "csv": {
        "enabled": True,
        "delimiter": ",",
        "encoding": "utf-8"
    },
    "pdf": {
        "enabled": True,
        "page_size": "A4",
        "orientation": "landscape"
    },
    "json": {
        "enabled": True,
        "indent": 2
    }
}

# ======================
# LOGGING CONFIGURATION
# ======================

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(lineno)d - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG" if DEBUG else "INFO",
            "formatter": "detailed",
            "filename": LOGS_DIR / "app.log",
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": LOGS_DIR / "error.log",
            "maxBytes": 10485760,
            "backupCount": 5
        }
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["console", "file", "error_file"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True
        },
        "uvicorn": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False
        },
        "sqlalchemy": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": False
        }
    }
}

# ======================
# API CONFIGURATION
# ======================

API_CONFIG = {
    "title": APP_NAME,
    "version": APP_VERSION,
    "description": APP_DESCRIPTION,
    "docs_url": "/docs" if DEBUG else None,
    "redoc_url": "/redoc" if DEBUG else None,
    "openapi_url": "/openapi.json" if DEBUG else None
}

# API rate limits (per endpoint)
API_RATE_LIMITS = {
    "default": "100/minute",
    "upload": "10/minute",
    "export": "20/hour",
    "login": "5/minute",
    "analytics": "30/minute"
}

# ======================
# CACHE CONFIGURATION
# ======================

CACHE_CONFIG = {
    "enabled": True,
    "type": "memory",  # memory, redis, file
    "ttl": 300,  # seconds
    "max_size": 100,  # max items in cache
    "redis_url": os.environ.get("REDIS_URL", "redis://localhost:6379/0")
}

# ======================
# NOTIFICATION SETTINGS
# ======================

NOTIFICATION_CONFIG = {
    "enabled": True,
    "methods": ["email", "sms", "in_app"],
    "email": {
        "smtp_host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.environ.get("SMTP_PORT", 587)),
        "smtp_user": os.environ.get("SMTP_USER", ""),
        "smtp_password": os.environ.get("SMTP_PASSWORD", ""),
        "from_email": os.environ.get("FROM_EMAIL", "noreply@health.gov"),
        "use_tls": True
    },
    "sms": {
        "provider": os.environ.get("SMS_PROVIDER", "twilio"),
        "api_key": os.environ.get("SMS_API_KEY", ""),
        "from_number": os.environ.get("SMS_FROM_NUMBER", "")
    },
    "alert_channels": {
        "critical": ["email", "sms", "in_app"],
        "high": ["email", "in_app"],
        "medium": ["in_app"],
        "low": ["in_app"]
    }
}

# ======================
# MAP CONFIGURATION
# ======================

MAP_CONFIG = {
    "center_lat": -19.0,  # Zimbabwe center
    "center_lng": 29.0,
    "zoom": 7,
    "tile_layer": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    "attribution": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a>"
}

# ======================
# DASHBOARD CONFIGURATION
# ======================

DASHBOARD_CONFIG = {
    "refresh_interval": 300,  # seconds
    "default_date_range": 12,  # weeks
    "charts_per_row": 3,
    "max_alerts_display": 10,
    "enable_auto_refresh": True,
    "default_view": "facility"  # facility, district, province, national
}

# ======================
# DATABASE CONFIGURATION
# ======================

DATABASE_CONFIG = {
    "url": f"sqlite:///{DATABASE_PATH}",
    "pool_size": 10,
    "max_overflow": 20,
    "echo": DEBUG,
    "connect_args": {"check_same_thread": False} if "sqlite" in str(DATABASE_PATH) else {}
}

# ======================
# BACKUP CONFIGURATION
# ======================

BACKUP_CONFIG = {
    "enabled": True,
    "interval_days": 1,
    "backup_dir": DATA_DIR / "backups",
    "max_backups": 30,
    "compress": True,
    "include_uploads": True
}

# ======================
# FEATURE FLAGS
# ======================

FEATURES = {
    "enable_alerts": True,
    "enable_analytics": True,
    "enable_maps": True,
    "enable_exports": True,
    "enable_notifications": False,
    "enable_api": True,
    "enable_bulk_upload": True,
    "enable_data_validation": True,
    "enable_trend_analysis": True,
    "enable_predictive_analytics": False
}

# ======================
# ENVIRONMENT-SPECIFIC OVERRIDES
# ======================

def load_environment_config():
    """Load environment-specific configuration"""
    env = os.environ.get("ENVIRONMENT", "development").lower()
    
    config_overrides = {
        "development": {
            "DEBUG": True,
            "TESTING": False,
            "RATE_LIMIT_ENABLED": False,
            "CACHE_CONFIG": {"enabled": False}
        },
        "testing": {
            "DEBUG": True,
            "TESTING": True,
            "DATABASE_PATH": DATA_DIR / "test.db",
            "RATE_LIMIT_ENABLED": False,
            "FEATURES": {k: False for k in FEATURES.keys()}  # Disable all features in test
        },
        "production": {
            "DEBUG": False,
            "TESTING": False,
            "RATE_LIMIT_ENABLED": True,
            "CACHE_CONFIG": {"enabled": True, "type": "redis"}
        }
    }
    
    return config_overrides.get(env, {})

# Apply environment overrides
ENV_CONFIG = load_environment_config()
locals().update(ENV_CONFIG)

# ======================
# CONFIGURATION VALIDATION
# ======================

def validate_config():
    """Validate critical configuration settings"""
    errors = []
    
    # Check secret key in production
    if not DEBUG and SECRET_KEY == "change-this-in-production-please":
        errors.append("SECRET_KEY must be changed in production")
    
    # Check directories exist
    for directory in [DATA_DIR, UPLOAD_DIR, EXPORTS_DIR, LOGS_DIR]:
        if not directory.exists():
            errors.append(f"Directory does not exist: {directory}")
    
    # Check database path is writable
    try:
        test_file = DATABASE_PATH.parent / "test_write.tmp"
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        errors.append(f"Cannot write to database directory: {e}")
    
    if errors:
        error_msg = "\n".join(errors)
        raise RuntimeError(f"Configuration validation failed:\n{error_msg}")
    
    return True

# Validate on import (but not in testing)
if not TESTING:
    validate_config()

# ======================
# HELPER FUNCTIONS
# ======================

def get_config_value(key: str, default: Any = None) -> Any:
    """Get configuration value by key"""
    return globals().get(key, default)


def get_facility_type_name(facility_type_id: str) -> str:
    """Get display name for facility type"""
    for ft in FACILITY_TYPES:
        if ft["id"] == facility_type_id:
            return ft["name"]
    return facility_type_id


def get_user_role_name(role_id: str) -> str:
    """Get display name for user role"""
    for role in USER_ROLES:
        if role["id"] == role_id:
            return role["name"]
    return role_id


def get_alert_threshold(alert_type: str, level: str = "warning") -> float:
    """Get alert threshold value"""
    if alert_type in ALERT_THRESHOLDS:
        return ALERT_THRESHOLDS[alert_type].get(level, 0)
    return 0


def get_performance_indicator_config(indicator: str) -> Dict:
    """Get performance indicator configuration"""
    for category, config in PERFORMANCE_INDICATORS.items():
        if indicator in config.get("indicators", []):
            return {
                "category": category,
                "category_name": config["name"],
                "weight": config["weight"]
            }
    return {}


def get_report_section_fields(section_id: str) -> List[str]:
    """Get field list for a report section"""
    for section in REPORT_SECTIONS:
        if section["id"] == section_id:
            return section["fields"]
    return []


def get_all_metric_fields() -> List[str]:
    """Get list of all metric fields"""
    fields = []
    for section in REPORT_SECTIONS:
        fields.extend(section["fields"])
    return fields


def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled"""
    return FEATURES.get(feature, False)


# ======================
# EXPORT CONFIGURATION
# ======================

__all__ = [
    # Base paths
    'BASE_DIR', 'DATA_DIR', 'UPLOAD_DIR', 'STATIC_DIR', 'TEMPLATES_DIR',
    'EXPORTS_DIR', 'LOGS_DIR', 'DATABASE_PATH',
    
    # App settings
    'APP_NAME', 'APP_VERSION', 'APP_DESCRIPTION', 'DEBUG', 'TESTING',
    'HOST', 'PORT', 'WORKERS', 'SECRET_KEY', 'ALGORITHM',
    'ACCESS_TOKEN_EXPIRE_MINUTES', 'SESSION_MAX_AGE',
    'ALLOWED_ORIGINS', 'ALLOWED_HOSTS',
    'RATE_LIMIT_ENABLED', 'RATE_LIMIT_REQUESTS', 'RATE_LIMIT_WINDOW',
    
    # File upload
    'MAX_FILE_SIZE', 'ALLOWED_EXTENSIONS', 'UPLOAD_CHUNK_SIZE',
    'MAX_FILENAME_LENGTH', 'CLEANUP_DAYS',
    
    # Facility types
    'FACILITY_TYPES', 'FACILITY_TYPE_CHOICES',
    
    # User roles
    'USER_ROLES', 'USER_ROLE_CHOICES', 'ROLE_PERMISSIONS',
    
    # Report sections
    'REPORT_SECTIONS',
    
    # Alert thresholds
    'ALERT_THRESHOLDS',
    
    # Performance targets
    'DEFAULT_TARGETS',
    
    # Performance indicators
    'PERFORMANCE_INDICATORS',
    
    # Data quality
    'DATA_QUALITY_RULES',
    
    # Visualization
    'VISUALIZATION_CONFIG',
    
    # Export
    'EXPORT_CONFIG',
    
    # Logging
    'LOGGING_CONFIG',
    
    # API
    'API_CONFIG', 'API_RATE_LIMITS',
    
    # Cache
    'CACHE_CONFIG',
    
    # Notifications
    'NOTIFICATION_CONFIG',
    
    # Map
    'MAP_CONFIG',
    
    # Dashboard
    'DASHBOARD_CONFIG',
    
    # Database
    'DATABASE_CONFIG',
    
    # Backup
    'BACKUP_CONFIG',
    
    # Features
    'FEATURES',
    
    # Helper functions
    'get_config_value', 'get_facility_type_name', 'get_user_role_name',
    'get_alert_threshold', 'get_performance_indicator_config',
    'get_report_section_fields', 'get_all_metric_fields', 'is_feature_enabled'
]

# ======================
# MAIN TEST FUNCTION
# ======================

if __name__ == "__main__":
    print(f"Configuration for {APP_NAME} v{APP_VERSION}")
    print(f"Environment: {'DEBUG' if DEBUG else 'PRODUCTION'}")
    print(f"Database: {DATABASE_PATH}")
    print(f"Upload directory: {UPLOAD_DIR}")
    
    print("\nFacility Types:")
    for ft in FACILITY_TYPES:
        print(f"  - {ft['name']} ({ft['id']})")
    
    print("\nUser Roles:")
    for role in USER_ROLES:
        print(f"  - {role['name']} ({role['id']})")
    
    print(f"\nFeatures enabled: {sum(FEATURES.values())}/{len(FEATURES)}")
    
    print("\nConfiguration validation: PASSED")