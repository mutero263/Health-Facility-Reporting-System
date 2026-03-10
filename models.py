"""
Data Models for Health Facility Reporting System
Pydantic v2 models for data validation and serialization
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import re
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ======================
# ENUMS AND CONSTANTS
# ======================

class FacilityType:
    """Facility type constants"""
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    RHC = "rhc"  # Rural Health Centre
    UHC = "uhc"  # Urban Health Centre
    DISPENSARY = "dispensary"
    HEALTH_POST = "health_post"
    
    @classmethod
    def values(cls):
        return [cls.HOSPITAL, cls.CLINIC, cls.RHC, cls.UHC, cls.DISPENSARY, cls.HEALTH_POST]


class UserRole:
    """User role constants"""
    ADMIN = "admin"
    DISTRICT_MANAGER = "district_manager"
    FACILITY_MANAGER = "facility_manager"
    DATA_ENTRY = "data_entry"
    PUBLIC_HEALTH_OFFICER = "public_health_officer"
    VIEWER = "viewer"
    
    @classmethod
    def values(cls):
        return [cls.ADMIN, cls.DISTRICT_MANAGER, cls.FACILITY_MANAGER, 
                cls.DATA_ENTRY, cls.PUBLIC_HEALTH_OFFICER, cls.VIEWER]


class AlertSeverity:
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    
    @classmethod
    def values(cls):
        return [cls.CRITICAL, cls.HIGH, cls.MEDIUM, cls.LOW, cls.INFO]


class AlertType:
    """Alert type categories"""
    DATA_QUALITY = "data_quality"
    PERFORMANCE = "performance"
    DISEASE_SURVEILLANCE = "disease_surveillance"
    STOCK_OUT = "stock_out"
    OUTBREAK = "outbreak"
    TARGET = "target"
    
    @classmethod
    def values(cls):
        return [cls.DATA_QUALITY, cls.PERFORMANCE, cls.DISEASE_SURVEILLANCE,
                cls.STOCK_OUT, cls.OUTBREAK, cls.TARGET]


# ======================
# HELPER CLASSES
# ======================

class FractionField:
    """Helper class for fraction fields (e.g., '6/6', '0/1')"""
    
    @staticmethod
    def validate(v: str) -> str:
        """Validate and clean fraction string"""
        if not v:
            return "0/0"
        v = str(v).strip()
        pattern = r'^\d+/\d+$'
        if re.match(pattern, v):
            return v
        numbers = re.findall(r'\d+', v)
        if len(numbers) == 2:
            return f"{numbers[0]}/{numbers[1]}"
        return "0/0"
    
    @staticmethod
    def get_numerator(v: str) -> int:
        """Extract numerator from fraction"""
        if isinstance(v, str) and '/' in v:
            try:
                return int(v.split('/')[0])
            except:
                return 0
        return 0
    
    @staticmethod
    def get_denominator(v: str) -> int:
        """Extract denominator from fraction"""
        if isinstance(v, str) and '/' in v:
            try:
                return int(v.split('/')[1])
            except:
                return 0
        return 0
    
    @staticmethod
    def get_rate(v: str) -> float:
        """Calculate rate from fraction"""
        num = FractionField.get_numerator(v)
        den = FractionField.get_denominator(v)
        return num / den if den > 0 else 0.0


# ======================
# BASE MODELS
# ======================

class BaseModelWithTimestamps(BaseModel):
    """Base model with timestamp fields"""
    model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda v: v.isoformat() if v else None})
    
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


# ======================
# FACILITY MODELS
# ======================

class FacilityBase(BaseModel):
    """Base facility model"""
    name: str = Field(..., description="Facility name", min_length=2, max_length=200)
    type: str = Field(..., description="Facility type")
    district: str = Field(..., description="District name", min_length=2, max_length=100)
    province: str = Field(..., description="Province name", min_length=2, max_length=100)
    catchment_population: Optional[int] = Field(default=0, description="Catchment population", ge=0)
    latitude: Optional[float] = Field(default=None, description="Latitude coordinate", ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, description="Longitude coordinate", ge=-180, le=180)
    active: bool = Field(default=True, description="Whether facility is active")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Validate facility type"""
        if v not in FacilityType.values():
            raise ValueError(f"Invalid facility type. Must be one of: {FacilityType.values()}")
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate facility name"""
        if not v or not v.strip():
            raise ValueError('Facility name cannot be empty')
        return v.strip()


class FacilityCreate(FacilityBase):
    """Model for creating a facility"""
    pass


class FacilityUpdate(BaseModel):
    """Model for updating a facility"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    type: Optional[str] = Field(None)
    district: Optional[str] = Field(None, min_length=2, max_length=100)
    province: Optional[str] = Field(None, min_length=2, max_length=100)
    catchment_population: Optional[int] = Field(None, ge=0)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    active: Optional[bool] = Field(None)
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Validate facility type if provided"""
        if v is not None and v not in FacilityType.values():
            raise ValueError(f"Invalid facility type. Must be one of: {FacilityType.values()}")
        return v
    
    @model_validator(mode='after')
    def validate_at_least_one(self):
        """Ensure at least one field is provided for update"""
        fields_to_check = [
            self.name, self.type, self.district, self.province,
            self.catchment_population, self.latitude, self.longitude, self.active
        ]
        if not any(f is not None for f in fields_to_check):
            raise ValueError('At least one field must be provided for update')
        return self


class Facility(FacilityBase, BaseModelWithTimestamps):
    """Complete facility model"""
    id: int = Field(..., description="Facility ID")


class FacilitySummary(BaseModel):
    """Facility summary for listings"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    type: str
    district: str
    province: str
    active: bool
    last_report_week: Optional[int] = None
    last_report_year: Optional[int] = None
    weeks_reported: Optional[int] = 0
    opd_visits: Optional[int] = 0
    institutional_deliveries: Optional[int] = 0
    anc_contacts: Optional[int] = 0
    reporting_rate: Optional[float] = 0
    performance_score: Optional[float] = 0


# ======================
# WEEKLY REPORT MODELS
# ======================

class WeeklyReportBase(BaseModel):
    """Base weekly report model"""
    model_config = ConfigDict(from_attributes=True)
    
    # Metadata
    facility_id: int = Field(..., description="Facility ID")
    week: int = Field(..., description="Week number (1-53)", ge=1, le=53)
    year: int = Field(..., description="Year", ge=2000, le=2100)
    report_date: Optional[datetime] = Field(default_factory=datetime.now)
    submitted_by: Optional[int] = Field(None, description="User ID who submitted the report")
    notes: Optional[str] = Field(None, description="Additional notes", max_length=500)
    
    # RDNS Metrics
    malaria_suspected: str = Field(default="0/0", description="Malaria suspected cases")
    malaria_tested: str = Field(default="0/0", description="Malaria tested")
    malaria_positive: str = Field(default="0/0", description="Malaria positive")
    malaria_uncomplicated: int = Field(default=0, description="Uncomplicated malaria cases", ge=0)
    malaria_severe: int = Field(default=0, description="Severe malaria cases", ge=0)
    malaria_death: int = Field(default=0, description="Malaria deaths", ge=0)
    malaria_history_travel: str = Field(default="No", description="History of travel")
    diarrhoea: str = Field(default="0/0", description="Diarrhoea cases")
    dysentery: str = Field(default="0/0", description="Dysentery cases")
    suspected_dysentery: str = Field(default="0/0", description="Suspected dysentery")
    influenza: str = Field(default="0/0", description="Influenza cases")
    dog_bite: int = Field(default=0, description="Dog bite cases", ge=0)
    kwashiorkor: int = Field(default=0, description="Kwashiorkor cases", ge=0)
    marasmus: int = Field(default=0, description="Marasmus cases", ge=0)
    bilharzia: int = Field(default=0, description="Bilharzia cases", ge=0)
    maternal_death: int = Field(default=0, description="Maternal deaths", ge=0)
    perinatal_death: int = Field(default=0, description="Perinatal deaths", ge=0)
    
    # VHW Metrics
    vhw_malaria_suspected: str = Field(default="0/0", description="VHW Malaria suspected")
    vhw_malaria_tested: str = Field(default="0/0", description="VHW Malaria tested")
    vhw_malaria_positive: str = Field(default="0/0", description="VHW Malaria positive")
    vhw_diarrhoea: str = Field(default="0/0", description="VHW Diarrhoea")
    vhw_dysentery: str = Field(default="0/0", description="VHW Dysentery")
    
    # AEFI Metrics
    aefi: int = Field(default=0, description="Adverse Events Following Immunization", ge=0)
    afp: int = Field(default=0, description="Acute Flaccid Paralysis", ge=0)
    nnt: int = Field(default=0, description="Neonatal Tetanus", ge=0)
    measles: int = Field(default=0, description="Measles cases", ge=0)
    
    # OPD Metrics
    drs_resigned: int = Field(default=0, description="Doctors resigned", ge=0)
    nurses_resigned: int = Field(default=0, description="Nurses resigned", ge=0)
    casualty_visits: int = Field(default=0, description="Casualty visits", ge=0)
    opd_visits: int = Field(default=0, description="OPD visits", ge=0)
    in_patients_admissions: int = Field(default=0, description="In-patient admissions", ge=0)
    major_operations: int = Field(default=0, description="Major operations", ge=0)
    c_sections: int = Field(default=0, description="C-sections performed", ge=0)
    renal_dialysis: int = Field(default=0, description="Renal dialysis sessions", ge=0)
    
    # Maternal Health
    anc_contacts: int = Field(default=0, description="ANC contacts", ge=0)
    fp_clients: int = Field(default=0, description="Family planning clients", ge=0)
    pnc_attendees: int = Field(default=0, description="PNC attendees", ge=0)
    institutional_deliveries: int = Field(default=0, description="Institutional deliveries", ge=0)
    home_deliveries: int = Field(default=0, description="Home deliveries", ge=0)
    still_births: int = Field(default=0, description="Still births", ge=0)
    
    # Child Health
    children_vaccinated_penta3: int = Field(default=0, description="Children vaccinated Penta3", ge=0)
    under5_sam: int = Field(default=0, description="Under 5 with SAM", ge=0)
    under5_mam: int = Field(default=0, description="Under 5 with MAM", ge=0)
    children_vitamin_a: int = Field(default=0, description="Children given Vitamin A", ge=0)
    under5_deaths: int = Field(default=0, description="Under 5 deaths", ge=0)
    
    # HIV/TB
    hiv_tested: int = Field(default=0, description="HIV tested", ge=0)
    hiv_positive: int = Field(default=0, description="HIV positive", ge=0)
    tb_new_relapse: int = Field(default=0, description="TB new and relapse", ge=0)
    tb_screened: int = Field(default=0, description="TB screened", ge=0)
    
    # Other
    institutional_deaths: int = Field(default=0, description="Institutional deaths", ge=0)
    functional_ambulance: int = Field(default=0, description="Functional ambulances", ge=0)
    xray_patients: int = Field(default=0, description="X-ray patients", ge=0)
    tracer_medicines_stock: int = Field(default=0, description="Tracer medicines with 2+ months stock", ge=0)
    
    @field_validator('malaria_history_travel')
    @classmethod
    def validate_travel_history(cls, v):
        """Validate travel history field"""
        valid_values = ['Yes', 'No', 'Unknown']
        if v not in valid_values:
            return 'Unknown'
        return v
    
    @field_validator('malaria_suspected', 'malaria_tested', 'malaria_positive',
                     'diarrhoea', 'dysentery', 'suspected_dysentery', 'influenza',
                     'vhw_malaria_suspected', 'vhw_malaria_tested', 'vhw_malaria_positive',
                     'vhw_diarrhoea', 'vhw_dysentery')
    @classmethod
    def validate_fraction(cls, v):
        """Validate fraction fields"""
        return FractionField.validate(v)
    
    @model_validator(mode='after')
    def validate_malaria_consistency(self):
        """Validate malaria data consistency"""
        suspected_num = FractionField.get_numerator(self.malaria_suspected)
        tested_num = FractionField.get_numerator(self.malaria_tested)
        positive_num = FractionField.get_numerator(self.malaria_positive)
        
        if tested_num > suspected_num and suspected_num > 0:
            self.malaria_tested = f"{suspected_num}/{FractionField.get_denominator(self.malaria_tested)}"
        if positive_num > tested_num and tested_num > 0:
            self.malaria_positive = f"{tested_num}/{FractionField.get_denominator(self.malaria_positive)}"
        return self
    
    @model_validator(mode='after')
    def validate_delivery_consistency(self):
        """Validate delivery data consistency"""
        if self.still_births > self.institutional_deliveries:
            self.still_births = self.institutional_deliveries
        return self


class WeeklyReportCreate(WeeklyReportBase):
    """Model for creating a weekly report"""
    pass


class WeeklyReportUpdate(BaseModel):
    """Model for updating a weekly report - partial updates"""
    model_config = ConfigDict(from_attributes=True)
    
    malaria_suspected: Optional[str] = None
    malaria_tested: Optional[str] = None
    malaria_positive: Optional[str] = None
    malaria_uncomplicated: Optional[int] = None
    malaria_severe: Optional[int] = None
    malaria_death: Optional[int] = None
    malaria_history_travel: Optional[str] = None
    diarrhoea: Optional[str] = None
    dysentery: Optional[str] = None
    suspected_dysentery: Optional[str] = None
    influenza: Optional[str] = None
    dog_bite: Optional[int] = None
    kwashiorkor: Optional[int] = None
    marasmus: Optional[int] = None
    bilharzia: Optional[int] = None
    maternal_death: Optional[int] = None
    perinatal_death: Optional[int] = None
    vhw_malaria_suspected: Optional[str] = None
    vhw_malaria_tested: Optional[str] = None
    vhw_malaria_positive: Optional[str] = None
    vhw_diarrhoea: Optional[str] = None
    vhw_dysentery: Optional[str] = None
    aefi: Optional[int] = None
    afp: Optional[int] = None
    nnt: Optional[int] = None
    measles: Optional[int] = None
    drs_resigned: Optional[int] = None
    nurses_resigned: Optional[int] = None
    casualty_visits: Optional[int] = None
    opd_visits: Optional[int] = None
    in_patients_admissions: Optional[int] = None
    major_operations: Optional[int] = None
    c_sections: Optional[int] = None
    renal_dialysis: Optional[int] = None
    anc_contacts: Optional[int] = None
    fp_clients: Optional[int] = None
    pnc_attendees: Optional[int] = None
    institutional_deliveries: Optional[int] = None
    home_deliveries: Optional[int] = None
    still_births: Optional[int] = None
    children_vaccinated_penta3: Optional[int] = None
    under5_sam: Optional[int] = None
    under5_mam: Optional[int] = None
    children_vitamin_a: Optional[int] = None
    under5_deaths: Optional[int] = None
    hiv_tested: Optional[int] = None
    hiv_positive: Optional[int] = None
    tb_new_relapse: Optional[int] = None
    tb_screened: Optional[int] = None
    institutional_deaths: Optional[int] = None
    functional_ambulance: Optional[int] = None
    xray_patients: Optional[int] = None
    tracer_medicines_stock: Optional[int] = None
    notes: Optional[str] = None
    
    @field_validator('malaria_history_travel')
    @classmethod
    def validate_travel_history(cls, v):
        """Validate travel history field if provided"""
        if v is not None:
            valid_values = ['Yes', 'No', 'Unknown']
            if v not in valid_values:
                return 'Unknown'
        return v
    
    @field_validator('malaria_suspected', 'malaria_tested', 'malaria_positive',
                     'diarrhoea', 'dysentery', 'suspected_dysentery', 'influenza',
                     'vhw_malaria_suspected', 'vhw_malaria_tested', 'vhw_malaria_positive',
                     'vhw_diarrhoea', 'vhw_dysentery')
    @classmethod
    def validate_fraction(cls, v):
        """Validate fraction fields if provided"""
        if v is not None:
            return FractionField.validate(v)
        return v


class WeeklyReport(WeeklyReportBase, BaseModelWithTimestamps):
    """Complete weekly report model"""
    id: int = Field(..., description="Report ID")
    data_quality_score: Optional[float] = Field(default=100.0, description="Data quality score (0-100)")
    
    @property
    def malaria_positivity_rate(self) -> float:
        """Calculate malaria positivity rate"""
        return FractionField.get_rate(self.malaria_positive)
    
    @property
    def malaria_testing_rate(self) -> float:
        """Calculate malaria testing rate"""
        suspected = FractionField.get_numerator(self.malaria_suspected)
        tested = FractionField.get_numerator(self.malaria_tested)
        return tested / suspected if suspected > 0 else 0.0
    
    @property
    def institutional_delivery_rate(self) -> float:
        """Calculate institutional delivery rate"""
        total = self.institutional_deliveries + self.home_deliveries
        return self.institutional_deliveries / total if total > 0 else 0.0


class WeeklyReportWithFacility(WeeklyReport):
    """Weekly report with facility information"""
    facility_name: str
    facility_type: str
    district: str
    province: str


# ======================
# REPORT SUMMARY MODELS
# ======================

class ReportSummary(BaseModel):
    """Report summary statistics for dashboard"""
    model_config = ConfigDict(from_attributes=True)
    
    total_reports: int = 0
    facilities_reporting: int = 0
    total_facilities: int = 0
    reporting_rate: float = 0
    total_opd: int = 0
    total_deliveries: int = 0
    total_anc: int = 0
    total_fp: int = 0
    total_pnc: int = 0
    total_hiv_tested: int = 0
    total_vaccinated: int = 0
    total_tb_screened: int = 0
    total_malaria_positive: int = 0
    avg_opd: float = 0
    week: Optional[int] = None
    year: Optional[int] = None
    district: Optional[str] = None


class FacilityComparison(BaseModel):
    """Facility comparison data"""
    model_config = ConfigDict(from_attributes=True)
    
    facility_id: int
    facility_name: str
    facility_type: str
    district: str
    metrics: Dict[str, Any]
    rank: Optional[int] = None
    score: Optional[float] = None


# ======================
# USER MODELS
# ======================

class UserBase(BaseModel):
    """Base user model"""
    model_config = ConfigDict(from_attributes=True)
    
    username: str = Field(..., description="Username", min_length=3, max_length=50)
    full_name: str = Field(..., description="Full name", min_length=2, max_length=100)
    email: Optional[str] = Field(None, description="Email address")
    role: str = Field(..., description="User role")
    facility_id: Optional[int] = Field(None, description="Associated facility ID (for facility-level users)")
    district: Optional[str] = Field(None, description="District (for district-level users)")
    province: Optional[str] = Field(None, description="Province (for province-level users)")
    active: bool = Field(default=True, description="Whether user is active")
    api_key: Optional[str] = Field(None, description="API key for programmatic access")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v.lower()
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Validate user role"""
        if v not in UserRole.values():
            raise ValueError(f"Invalid role. Must be one of: {UserRole.values()}")
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format if provided"""
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v
    
    @model_validator(mode='after')
    def validate_facility_or_district(self):
        """Ensure facility_id or district is set based on role"""
        if self.role in ['facility_manager', 'data_entry'] and not self.facility_id:
            raise ValueError(f'Users with role {self.role} must have a facility_id')
        if self.role == 'district_manager' and not self.district:
            raise ValueError('District managers must have a district')
        return self


class UserCreate(UserBase):
    """Model for creating a user"""
    password: str = Field(..., description="Password", min_length=8)


class UserUpdate(BaseModel):
    """Model for updating a user"""
    model_config = ConfigDict(from_attributes=True)
    
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = None
    role: Optional[str] = None
    facility_id: Optional[int] = None
    district: Optional[str] = None
    province: Optional[str] = None
    active: Optional[bool] = None
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Validate user role if provided"""
        if v and v not in UserRole.values():
            raise ValueError(f"Invalid role. Must be one of: {UserRole.values()}")
        return v


class User(UserBase, BaseModelWithTimestamps):
    """Complete user model"""
    id: int = Field(..., description="User ID")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")


class UserLogin(BaseModel):
    """User login model"""
    username: str
    password: str


class UserChangePassword(BaseModel):
    """Change password model"""
    old_password: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


# ======================
# ALERT MODELS
# ======================

class AlertBase(BaseModel):
    """Base alert model"""
    model_config = ConfigDict(from_attributes=True)
    
    facility_id: int = Field(..., description="Facility ID")
    week: Optional[int] = Field(None, description="Week number", ge=1, le=53)
    year: Optional[int] = Field(None, description="Year", ge=2000)
    alert_type: str = Field(..., description="Alert type")
    severity: str = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message", max_length=500)
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    
    @field_validator('alert_type')
    @classmethod
    def validate_alert_type(cls, v):
        """Validate alert type"""
        if v not in AlertType.values():
            raise ValueError(f"Invalid alert type. Must be one of: {AlertType.values()}")
        return v
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        """Validate alert severity"""
        if v not in AlertSeverity.values():
            raise ValueError(f"Invalid severity. Must be one of: {AlertSeverity.values()}")
        return v


class AlertCreate(AlertBase):
    """Model for creating an alert"""
    pass


class Alert(AlertBase, BaseModelWithTimestamps):
    """Complete alert model"""
    id: int = Field(..., description="Alert ID")
    resolved: bool = Field(default=False, description="Whether alert is resolved")
    resolved_by: Optional[int] = Field(None, description="User ID who resolved the alert")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")


class AlertWithFacility(Alert):
    """Alert with facility information"""
    facility_name: str
    district: str


class AlertSummary(BaseModel):
    """Alert summary statistics"""
    model_config = ConfigDict(from_attributes=True)
    
    total_alerts: int
    critical_unresolved: int
    high_unresolved: int
    medium_unresolved: int
    low_unresolved: int
    facilities_with_alerts: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]


# ======================
# DASHBOARD AND ANALYSIS MODELS
# ======================

class DashboardSummary(BaseModel):
    """Dashboard summary statistics"""
    model_config = ConfigDict(from_attributes=True)
    
    total_facilities: int
    facilities_reporting: int
    reporting_rate: float
    total_opd_visits: int
    total_deliveries: int
    total_anc_contacts: int
    total_hiv_tested: int
    total_malaria_cases: int
    alerts_critical: int
    alerts_high: int
    week: int
    year: int


class FacilityPerformance(BaseModel):
    """Facility performance indicators"""
    model_config = ConfigDict(from_attributes=True)
    
    facility_id: int
    facility_name: str
    district: str
    malaria_testing_rate: float
    malaria_positivity_rate: float
    institutional_delivery_rate: float
    anc_coverage: float
    pnc_coverage: float
    hiv_testing_rate: float
    performance_score: float
    rank: Optional[int] = None


class TimeSeriesDataPoint(BaseModel):
    """Time series data point"""
    period: str
    year: int
    week: int
    value: float


class TrendAnalysis(BaseModel):
    """Trend analysis results"""
    model_config = ConfigDict(from_attributes=True)
    
    metric: str
    facility_id: Optional[int]
    facility_name: Optional[str]
    district: Optional[str]
    data_points: List[TimeSeriesDataPoint]
    trend_direction: str
    percentage_change: float
    volatility: float


class ComparisonResult(BaseModel):
    """Facility comparison result"""
    model_config = ConfigDict(from_attributes=True)
    
    metric: str
    rankings: List[Dict[str, Any]]
    best_performer: Dict[str, Any]
    needs_improvement: Dict[str, Any]
    district_average: float


# ======================
# TARGET MODELS
# ======================

class TargetBase(BaseModel):
    """Base target model"""
    model_config = ConfigDict(from_attributes=True)
    
    metric: str = Field(..., description="Metric name")
    target_value: float = Field(..., description="Target value", ge=0)
    year: Optional[int] = Field(None, description="Target year", ge=2000)
    facility_id: Optional[int] = Field(None, description="Facility ID (for facility-specific targets)")
    district: Optional[str] = Field(None, description="District (for district-level targets)")
    province: Optional[str] = Field(None, description="Province (for province-level targets)")
    
    @model_validator(mode='after')
    def validate_scope(self):
        """Ensure exactly one scope is set"""
        scopes = [self.facility_id, self.district, self.province]
        set_count = sum(1 for s in scopes if s is not None)
        if set_count != 1:
            raise ValueError('Exactly one of facility_id, district, or province must be set')
        return self


class TargetCreate(TargetBase):
    """Model for creating a target"""
    pass


class TargetUpdate(BaseModel):
    """Model for updating a target"""
    model_config = ConfigDict(from_attributes=True)
    
    target_value: Optional[float] = Field(None, ge=0)
    year: Optional[int] = Field(None, ge=2000)


class Target(TargetBase, BaseModelWithTimestamps):
    """Complete target model"""
    id: int = Field(..., description="Target ID")


# ======================
# EXPORT MODELS
# ======================

class ExportRequest(BaseModel):
    """Export request model"""
    model_config = ConfigDict(from_attributes=True)
    
    format: str = Field(..., description="Export format", pattern="^(excel|csv|pdf|json)$")
    facility_ids: Optional[List[int]] = Field(None, description="Facility IDs to export")
    district: Optional[str] = Field(None, description="District to export")
    start_week: int = Field(..., description="Start week", ge=1, le=53)
    start_year: int = Field(..., description="Start year", ge=2000)
    end_week: int = Field(..., description="End week", ge=1, le=53)
    end_year: int = Field(..., description="End year", ge=2000)
    metrics: Optional[List[str]] = Field(None, description="Metrics to include")
    
    @model_validator(mode='after')
    def validate_date_range(self):
        """Validate date range"""
        if (self.start_year > self.end_year) or (self.start_year == self.end_year and self.start_week > self.end_week):
            raise ValueError('Start date must be before end date')
        return self


class ExportResult(BaseModel):
    """Export result model"""
    model_config = ConfigDict(from_attributes=True)
    
    filename: str
    file_size: int
    download_url: str
    format: str
    generated_at: datetime


# ======================
# API RESPONSE MODELS
# ======================

class ApiResponse(BaseModel):
    """Standard API response wrapper"""
    model_config = ConfigDict(from_attributes=True)
    
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[List[str]] = None


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    model_config = ConfigDict(from_attributes=True)
    
    total: int
    page: int
    page_size: int
    total_pages: int
    data: List[Any]


# ======================
# CONFIGURATION MODELS
# ======================

class SystemSettings(BaseModel):
    """System settings model"""
    model_config = ConfigDict(from_attributes=True)
    
    alert_thresholds: Dict[str, Any]
    default_targets: Dict[str, float]
    data_quality_rules: Dict[str, Any]
    notification_settings: Dict[str, Any]
    updated_at: datetime


# ======================
# VALIDATION FUNCTIONS
# ======================

def validate_week_year(week: int, year: int) -> bool:
    """Validate week and year combination"""
    return 1 <= week <= 53 and 2000 <= year <= 2100


def validate_date_range(start_week: int, start_year: int, 
                        end_week: int, end_year: int) -> bool:
    """Validate date range"""
    if not validate_week_year(start_week, start_year):
        return False
    if not validate_week_year(end_week, end_year):
        return False
    if start_year > end_year:
        return False
    if start_year == end_year and start_week > end_week:
        return False
    return True