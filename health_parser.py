"""
Health Facility Report Parser
Parses text-based weekly health facility reports into structured data
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================
# FRACTION FIELD HELPER CLASS
# ======================

class FractionField:
    """Helper class for fraction fields (e.g., '6/6', '0/1')"""
    
    @staticmethod
    def validate(v: str) -> str:
        """Validate and clean fraction string"""
        if not v:
            return "0/0"
        
        # Convert to string and clean
        v = str(v).strip()
        
        # Check format
        pattern = r'^\d+/\d+$'
        if re.match(pattern, v):
            return v
        
        # Try to extract numbers
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
# DATA MODELS
# ======================

class ReportSection(Enum):
    """Sections within a health report"""
    RDNS = "rdns"  # Routine Data Notification System
    VHW = "vhw"    # Village Health Worker
    AEFI = "aefi"  # Adverse Events Following Immunization
    OPD = "opd"    # Outpatient Department
    MATERNAL = "maternal"
    CHILD = "child"
    OTHER = "other"


@dataclass
class HealthReport:
    """Structured health facility report"""
    # Metadata
    facility_name: str
    facility_id: Optional[int] = None
    week: int = 0
    year: int = datetime.now().year
    report_date: Optional[datetime] = None
    raw_text: str = ""
    
    # RDNS Section
    malaria_suspected: str = "0/0"
    malaria_tested: str = "0/0"
    malaria_positive: str = "0/0"
    malaria_uncomplicated: int = 0
    malaria_severe: int = 0
    malaria_death: int = 0
    malaria_history_travel: str = "No"
    diarrhoea: str = "0/0"
    dysentery: str = "0/0"
    suspected_dysentery: str = "0/0"
    influenza: str = "0/0"
    dog_bite: int = 0
    kwashiorkor: int = 0
    marasmus: int = 0
    bilharzia: int = 0
    maternal_death: int = 0
    perinatal_death: int = 0
    
    # VHW Section
    vhw_malaria_suspected: str = "0/0"
    vhw_malaria_tested: str = "0/0"
    vhw_malaria_positive: str = "0/0"
    vhw_diarrhoea: str = "0/0"
    vhw_dysentery: str = "0/0"
    
    # AEFI Section
    aefi: int = 0
    afp: int = 0  # Acute Flaccid Paralysis
    nnt: int = 0  # Neonatal Tetanus
    measles: int = 0
    
    # OPD Section
    drs_resigned: int = 0
    nurses_resigned: int = 0
    casualty_visits: int = 0
    opd_visits: int = 0
    in_patients_admissions: int = 0
    major_operations: int = 0
    c_sections: int = 0
    renal_dialysis: int = 0
    
    # Maternal Health
    anc_contacts: int = 0  # Antenatal Care
    fp_clients: int = 0    # Family Planning
    pnc_attendees: int = 0 # Postnatal Care
    institutional_deliveries: int = 0
    home_deliveries: int = 0
    still_births: int = 0
    maternal_deaths: int = 0
    
    # Child Health
    children_vaccinated_penta3: int = 0
    under5_sam: int = 0    # Severe Acute Malnutrition
    under5_mam: int = 0    # Moderate Acute Malnutrition
    children_vitamin_a: int = 0
    under5_deaths: int = 0
    
    # HIV/TB
    hiv_tested: int = 0
    hiv_positive: int = 0
    tb_new_relapse: int = 0
    tb_screened: int = 0
    
    # Other
    institutional_deaths: int = 0
    functional_ambulance: int = 0
    xray_patients: int = 0
    tracer_medicines_stock: int = 0
    
    # Additional metrics (catch-all for facility-specific fields)
    additional_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                result[key] = value
        return result
    
    def get_fraction_parts(self, field_name: str) -> Tuple[int, int]:
        """Get numerator and denominator from a fraction field"""
        value = getattr(self, field_name, "0/0")
        if isinstance(value, str) and '/' in value:
            parts = value.split('/')
            try:
                numerator = int(parts[0]) if parts[0].strip() else 0
                denominator = int(parts[1]) if len(parts) > 1 and parts[1].strip() else 0
                return numerator, denominator
            except ValueError:
                return 0, 0
        return 0, 0


# ======================
# PARSER PATTERNS
# ======================

# Facility name patterns
FACILITY_PATTERNS = [
    r'([A-Za-z\s]+(?:rhc|RHC|clinic|Clinic|hospital|Hospital|centre|Centre))',
    r'^([A-Za-z\s]+?)(?:\s+week|\s+Wk|\s+Weekly|\s+Report|\n|$)',
]

# Week patterns
WEEK_PATTERNS = [
    r'[Ww]eek\s*[:\-]?\s*(\d+)',
    r'Wk\s*[:\-]?\s*(\d+)',
    r'Week\s+(\d+)',
]

# Section headers
SECTION_PATTERNS = {
    ReportSection.RDNS: [r'RDNS', r'Routine Data', r'Weekly\s+RDNS'],
    ReportSection.VHW: [r'VHW', r'Village Health', r'VHW\s+report'],
    ReportSection.AEFI: [r'AEFI', r'Adverse Events'],
    ReportSection.OPD: [r'OPD', r'Outpatient', r'Weekly delivery service'],
}

# Metric patterns with various separators
METRIC_PATTERNS = {
    # Malaria
    'malaria_suspected': [
        r'Malaria\s+suspected\s*[:\-~=]?\s*(\d+/\d+)',
        r'Susp(?:ected)?\s+Malaria\s*[:\-~=]?\s*(\d+/\d+)',
        r'Suspected\s+Mal~?\s*[:\-~=]?\s*(\d+/\d+)',
    ],
    'malaria_tested': [
        r'Tested\s*[.,]?\s*(\d+/\d+)',
        r'Malaria\s+tested\s*[:\-~=]?\s*(\d+/\d+)',
    ],
    'malaria_positive': [
        r'Positive\s*[~]?\s*(\d+/\d+)',
        r'Confirmed\s+positive\s*[:\-~=]?\s*(\d+/\d+)',
        r'Malaria\s+positive\s*[:\-~=]?\s*(\d+/\d+)',
    ],
    'malaria_uncomplicated': [
        r'Uncomplicated\s+malaria\s*[:\-~=]?\s*(\d+)',
    ],
    'malaria_death': [
        r'Death\s*[~]?\s*(\d+/\d+)',
        r'Malaria\s+death\s*[:\-~=]?\s*(\d+)',
    ],
    'malaria_history_travel': [
        r'history\s+of\s+travel\s*[:\-~=]?\s*(No|Yes|None)',
        r'no\s+hx\s+of\s+travelling',
    ],
    
    # Diarrhea & Dysentery
    'diarrhoea': [
        r'Diarrhoea\s*[:\-~=]?\s*(\d+/\d+)',
        r'Diarrhea\s*[:\-~=]?\s*(\d+/\d+)',
    ],
    'dysentery': [
        r'Dysentery\s*[:\-~=]?\s*(\d+/\d+)',
    ],
    'suspected_dysentery': [
        r'Suspected\s+dysentery\s*[:\-~=]?\s*(\d+/\d+)',
    ],
    
    # Other diseases
    'influenza': [
        r'Influenza\s*[:\-~=]?\s*(\d+/\d+)',
    ],
    'dog_bite': [
        r'Dog\s+bite\s*[:\-~=]?\s*(\d+)',
    ],
    'kwashiorkor': [
        r'Kwashiorkor\s*[:\-~=]?\s*(\d+)',
    ],
    'marasmus': [
        r'Marasmus\s*[:\-~=]?\s*(\d+)',
    ],
    'bilharzia': [
        r'Bilharzia\s*[:\-~=]?\s*(\d+)',
    ],
    
    # Deaths
    'maternal_death': [
        r'Maternal\s+death\s*[:\-~=]?\s*(\d+)',
        r'Maternal\s+deaths?\s*[:\-~=]?\s*(\d+)',
    ],
    'perinatal_death': [
        r'Perinatal\s+death\s*[:\-~=]?\s*(\d+)',
    ],
    
    # VHW Section
    'vhw_malaria_suspected': [
        r'VHW.*?malaria\s+suspected\s*[:\-~=]?\s*(\d+/\d+)',
        r'VHW.*?Susp\s+Malaria\s*[:\-~=]?\s*(\d+/\d+)',
    ],
    'vhw_malaria_tested': [
        r'VHW.*?Tested\s*[.,]?\s*(\d+/\d+)',
    ],
    'vhw_malaria_positive': [
        r'VHW.*?Positive\s*[.:]?\s*(\d+/\d+)',
    ],
    'vhw_diarrhoea': [
        r'VHW.*?Diarrhoea\s*[:\-~=]?\s*(\d+/\d+)',
    ],
    
    # AEFI
    'aefi': [
        r'AEFI\s*[:\-~=]?\s*(\d+)',
    ],
    'afp': [
        r'AFP\s*[:\-~=]?\s*(\d+)',
    ],
    'nnt': [
        r'NNT\s*[:\-~=]?\s*(\d+)',
    ],
    'measles': [
        r'Measles\s*[:\-~=]?\s*(\d+)',
    ],
    
    # Staff
    'drs_resigned': [
        r'Dr(?:s)?\s+who\s+resigned\s*[:\-~=]?\s*(\d+)',
        r'No\s+of\s+Drs?\s+who\s+resigned\s*[:\-~=]?\s*(\d+)',
    ],
    'nurses_resigned': [
        r'nurses?\s+who\s+resigned\s*[:\-~=]?\s*(\d+)',
        r'No\s+of\s+nurses?\s+who\s+resigned\s*[:\-~=]?\s*(\d+)',
    ],
    
    # Visits & Admissions
    'casualty_visits': [
        r'pt?\s+who\s+visited\s+casualty\s*[:\-~=]?\s*(\d+)',
        r'casualty\s*[:\-~=]?\s*(\d+)',
    ],
    'opd_visits': [
        r'opd\s+visits?\s*[:\-~=]?\s*(\d+)',
        r'pts?\s+visiting\s+OPD\s*[:\-~=]?\s*(\d+)',
        r'OPD\s+visits?\s*[:\-~=]?\s*(\d+)',
    ],
    'in_patients_admissions': [
        r'in\s+patients?\s+admissions?\s*[:\-~=]?\s*(\d+)',
        r'pts?\s+admitted\s*[:\-~=]?\s*(\d+)',
    ],
    
    # Procedures
    'major_operations': [
        r'major\s+operations?\s+done\s*[:\-~=]?\s*(\d+)',
        r'major\s+ops?\s*[:\-~=]?\s*(\d+)',
    ],
    'c_sections': [
        r'c(?:aesarian)?\s*section\s+done\s*[:\-~=]?\s*(\d+)',
        r'c\/?section\s*[:\-~=]?\s*(\d+)',
    ],
    'renal_dialysis': [
        r'renal\s+dialysis\s+done\s*[:\-~=]?\s*(\d+)',
    ],
    
    # Maternal Health
    'anc_contacts': [
        r'ANC\s+contact\s*[:\-~=]?\s*(\d+)',
        r'No\s+of\s+ANC\s+contact\s*[:\-~=]?\s*(\d+)',
    ],
    'fp_clients': [
        r'(?:clients who received )?FP\s*[:\-~=]?\s*(\d+)',
        r'Family\s+planning\s*[:\-~=]?\s*(\d+)',
    ],
    'pnc_attendees': [
        r'PNC\s*[:\-~=]?\s*(\d+)',
        r'clients?\s+who\s+attended\s+PNC\s*[:\-~=]?\s*(\d+)',
    ],
    'institutional_deliveries': [
        r'institutional\s+deliver(?:ies|y)\s*[:\-~=]?\s*(\d+)',
        r'No\s+of\s+institutional\s+deliveries\s*[:\-~=]?\s*(\d+)',
    ],
    'home_deliveries': [
        r'home\s+delivery\s*[:\-~=]?\s*(\d+)',
        r'home\s+deliveries?\s*[:\-~=]?\s*(\d+)',
    ],
    'still_births': [
        r'still\s+birth\s*[:\-~=]?\s*(\d+)',
        r'still\s+births?\s*[:\-~=]?\s*(\d+)',
    ],
    
    # Child Health
    'children_vaccinated_penta3': [
        r'chn?\s+vaccinated\s+penta\s*3\.?\s*[:\-~=]?\s*(\d+)',
        r'children?\s+vaccinated\s+DPT³?\s*[:\-~=]?\s*(\d+)',
    ],
    'under5_sam': [
        r'under\s*5\s+s with SAM\s*[:\-~=]?\s*(\d+)',
        r'SAM\s*[:\-~=]?\s*(\d+)',
    ],
    'under5_mam': [
        r'under\s*5\s+s with MAM\s*[:\-~=]?\s*(\d+)',
        r'MAM\s*[:\-~=]?\s*(\d+)',
    ],
    'children_vitamin_a': [
        r'chn?\s+given\s+vit\s*A\s*[:\-~=]?\s*(\d+)',
        r'Vitamin\s+A\s*[:\-~=]?\s*(\d+)',
    ],
    'under5_deaths': [
        r'under\s*5\s+death\s*[:\-~=]?\s*(\d+)',
    ],
    
    # HIV/TB
    'hiv_tested': [
        r'tested\s+for\s+HIV\s*[:\-~=]?\s*(\d+)',
        r'No\s+of\s+tested\s+for\s+HIV\s*[:\-~=]?\s*(\d+)',
    ],
    'hiv_positive': [
        r'HIV\s+positive\s*[:\-~=]?\s*(\d+)',
    ],
    'tb_new_relapse': [
        r'Tb?\s+patients?\s+new\s+and\s+relapse\s*[:\-~=]?\s*(\d+)',
        r'TB\s+new\s+&\s+relapse\s*[:\-~=]?\s*(\d+)',
    ],
    'tb_screened': [
        r'pts?\s+screened\s+for\s+TB\s*[.\s]*(\d+)',
        r'screened\s+for\s+TB\s*[:\-~=]?\s*(\d+)',
    ],
    
    # Other
    'institutional_deaths': [
        r'institutional\s*[b]?death\s*[:\-~=]?\s*(\d+)',
        r'facility\s+death\s*[:\-~=]?\s*(\d+)',
    ],
    'functional_ambulance': [
        r'functional\s+ambulance\s*[:\-~=]?\s*(\d+)',
    ],
    'xray_patients': [
        r'pts?\s+who\s+receive\s+X-?ray\s*[:\-~=]?\s*(\d+)',
    ],
    'tracer_medicines_stock': [
        r'facility\*?\s+with\s+selected\s+tracer\s+medicines\s*[:\-~=]?\s*(\d+)',
    ],
}

# Patterns for zeros and missing data
ZERO_PATTERNS = [
    r'rest\s+zeros?',
    r'all\s+zeros?',
    r'the\s+rest\s+are\s+zeros?',
    r'others?\s+zero',
]


# ======================
# PARSER FUNCTIONS
# ======================

def extract_facility_name(text: str) -> Optional[str]:
    """Extract facility name from report text"""
    for pattern in FACILITY_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            name = match.group(1).strip()
            # Clean up common issues
            name = re.sub(r'\s+', ' ', name)
            return name
    return None


def extract_week(text: str) -> int:
    """Extract week number from report text"""
    for pattern in WEEK_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
    return 0


def extract_section(text: str, section: ReportSection) -> str:
    """Extract a specific section from the report"""
    patterns = SECTION_PATTERNS.get(section, [])
    for pattern in patterns:
        # Look for section header and capture until next section or end
        section_pattern = rf'{pattern}.*?(?=(?:{"|".join(sum(SECTION_PATTERNS.values(), []))}|$))'
        match = re.search(section_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(0)
    return ""


def parse_fraction(value: str) -> str:
    """Clean and validate fraction values"""
    return FractionField.validate(value)


def parse_integer(value: str) -> int:
    """Parse integer value from various formats"""
    if not value:
        return 0
    
    # Remove non-numeric characters
    cleaned = re.sub(r'[^\d]', '', value)
    
    try:
        return int(cleaned) if cleaned else 0
    except ValueError:
        return 0


def apply_zero_patterns(text: str, report: HealthReport):
    """Apply 'rest zeros' patterns to set unspecified fields to zero"""
    if re.search('|'.join(ZERO_PATTERNS), text, re.IGNORECASE):
        # Set all fraction fields to 0/0 if they're still empty
        fraction_fields = [
            'malaria_suspected', 'malaria_tested', 'malaria_positive',
            'diarrhoea', 'dysentery', 'influenza',
            'vhw_malaria_suspected', 'vhw_malaria_tested', 'vhw_malaria_positive',
            'vhw_diarrhoea'
        ]
        
        for field in fraction_fields:
            if getattr(report, field) == "":
                setattr(report, field, "0/0")
        
        # Set all integer fields to 0 if they're still empty
        for field, value in report.__dict__.items():
            if not field.startswith('_') and value == "" and not isinstance(value, str):
                setattr(report, field, 0)


def parse_health_report(text: str, facility_id: Optional[int] = None, 
                        default_week: int = 0, default_year: int = None) -> HealthReport:
    """
    Parse a health facility report from text
    
    Args:
        text: Raw report text
        facility_id: Optional facility ID (if known)
        default_week: Default week if not found
        default_year: Default year if not found
        
    Returns:
        HealthReport object with parsed data
    """
    if default_year is None:
        default_year = datetime.now().year
    
    # Create report object
    report = HealthReport(
        facility_name=extract_facility_name(text) or "Unknown Facility",
        facility_id=facility_id,
        week=extract_week(text) or default_week,
        year=default_year,
        report_date=datetime.now(),
        raw_text=text[:500]  # Store first 500 chars for reference
    )
    
    logger.info(f"Parsing report for facility: {report.facility_name}, Week: {report.week}")
    
    # Extract sections
    rdns_section = extract_section(text, ReportSection.RDNS)
    vhw_section = extract_section(text, ReportSection.VHW)
    aefi_section = extract_section(text, ReportSection.AEFI)
    opd_section = extract_section(text, ReportSection.OPD)
    
    # Parse each section
    if rdns_section:
        parse_rdns_section(rdns_section, report)
    
    if vhw_section:
        parse_vhw_section(vhw_section, report)
    
    if aefi_section:
        parse_aefi_section(aefi_section, report)
    
    if opd_section:
        parse_opd_section(opd_section, report)
    
    # Parse the full text for any remaining metrics
    parse_remaining_metrics(text, report)
    
    # Apply "rest zeros" patterns
    apply_zero_patterns(text, report)
    
    return report


def parse_rdns_section(section: str, report: HealthReport):
    """Parse RDNS section of the report"""
    logger.debug("Parsing RDNS section")
    
    # Malaria metrics
    for pattern in METRIC_PATTERNS['malaria_suspected']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.malaria_suspected = parse_fraction(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['malaria_tested']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.malaria_tested = parse_fraction(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['malaria_positive']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.malaria_positive = parse_fraction(match.group(1))
            break
    
    # Check for uncomplicated malaria
    for pattern in METRIC_PATTERNS['malaria_uncomplicated']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.malaria_uncomplicated = parse_integer(match.group(1))
            break
    
    # Malaria death
    for pattern in METRIC_PATTERNS['malaria_death']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            value = match.group(1)
            if '/' in value:
                # It's a fraction
                num, _ = parse_fraction(value).split('/')
                report.malaria_death = int(num)
            else:
                report.malaria_death = parse_integer(value)
            break
    
    # Travel history
    for pattern in METRIC_PATTERNS['malaria_history_travel']:
        if re.search(pattern, section, re.IGNORECASE):
            report.malaria_history_travel = "No"
            break
    
    # Diarrhoea
    for pattern in METRIC_PATTERNS['diarrhoea']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.diarrhoea = parse_fraction(match.group(1))
            break
    
    # Dysentery
    for pattern in METRIC_PATTERNS['dysentery']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.dysentery = parse_fraction(match.group(1))
            break
    
    # Suspected dysentery
    for pattern in METRIC_PATTERNS['suspected_dysentery']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.suspected_dysentery = parse_fraction(match.group(1))
            break
    
    # Influenza
    for pattern in METRIC_PATTERNS['influenza']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.influenza = parse_fraction(match.group(1))
            break
    
    # Dog bite
    for pattern in METRIC_PATTERNS['dog_bite']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.dog_bite = parse_integer(match.group(1))
            break
    
    # Kwashiorkor
    for pattern in METRIC_PATTERNS['kwashiorkor']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.kwashiorkor = parse_integer(match.group(1))
            break
    
    # Marasmus
    for pattern in METRIC_PATTERNS['marasmus']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.marasmus = parse_integer(match.group(1))
            break
    
    # Bilharzia
    for pattern in METRIC_PATTERNS['bilharzia']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.bilharzia = parse_integer(match.group(1))
            break
    
    # Maternal death
    for pattern in METRIC_PATTERNS['maternal_death']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.maternal_death = parse_integer(match.group(1))
            break
    
    # Perinatal death
    for pattern in METRIC_PATTERNS['perinatal_death']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.perinatal_death = parse_integer(match.group(1))
            break


def parse_vhw_section(section: str, report: HealthReport):
    """Parse VHW (Village Health Worker) section"""
    logger.debug("Parsing VHW section")
    
    # VHW Malaria suspected
    for pattern in METRIC_PATTERNS['vhw_malaria_suspected']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.vhw_malaria_suspected = parse_fraction(match.group(1))
            break
    
    # VHW Malaria tested
    for pattern in METRIC_PATTERNS['vhw_malaria_tested']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.vhw_malaria_tested = parse_fraction(match.group(1))
            break
    
    # VHW Malaria positive
    for pattern in METRIC_PATTERNS['vhw_malaria_positive']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.vhw_malaria_positive = parse_fraction(match.group(1))
            break
    
    # VHW Diarrhoea
    for pattern in METRIC_PATTERNS['vhw_diarrhoea']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.vhw_diarrhoea = parse_fraction(match.group(1))
            break


def parse_aefi_section(section: str, report: HealthReport):
    """Parse AEFI section"""
    logger.debug("Parsing AEFI section")
    
    # AEFI
    for pattern in METRIC_PATTERNS['aefi']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.aefi = parse_integer(match.group(1))
            break
    
    # AFP
    for pattern in METRIC_PATTERNS['afp']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.afp = parse_integer(match.group(1))
            break
    
    # NNT
    for pattern in METRIC_PATTERNS['nnt']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.nnt = parse_integer(match.group(1))
            break
    
    # Measles
    for pattern in METRIC_PATTERNS['measles']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.measles = parse_integer(match.group(1))
            break


def parse_opd_section(section: str, report: HealthReport):
    """Parse OPD section"""
    logger.debug("Parsing OPD section")
    
    # Staff
    for pattern in METRIC_PATTERNS['drs_resigned']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.drs_resigned = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['nurses_resigned']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.nurses_resigned = parse_integer(match.group(1))
            break
    
    # Visits
    for pattern in METRIC_PATTERNS['casualty_visits']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.casualty_visits = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['opd_visits']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.opd_visits = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['in_patients_admissions']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.in_patients_admissions = parse_integer(match.group(1))
            break
    
    # Procedures
    for pattern in METRIC_PATTERNS['major_operations']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.major_operations = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['c_sections']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.c_sections = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['renal_dialysis']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.renal_dialysis = parse_integer(match.group(1))
            break
    
    # Maternal Health
    for pattern in METRIC_PATTERNS['anc_contacts']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.anc_contacts = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['fp_clients']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.fp_clients = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['pnc_attendees']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.pnc_attendees = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['institutional_deliveries']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.institutional_deliveries = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['home_deliveries']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.home_deliveries = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['still_births']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.still_births = parse_integer(match.group(1))
            break
    
    # Child Health
    for pattern in METRIC_PATTERNS['children_vaccinated_penta3']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.children_vaccinated_penta3 = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['under5_sam']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.under5_sam = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['under5_mam']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.under5_mam = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['children_vitamin_a']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.children_vitamin_a = parse_integer(match.group(1))
            break
    
    # HIV/TB
    for pattern in METRIC_PATTERNS['hiv_tested']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.hiv_tested = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['tb_new_relapse']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.tb_new_relapse = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['tb_screened']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.tb_screened = parse_integer(match.group(1))
            break
    
    # Other
    for pattern in METRIC_PATTERNS['institutional_deaths']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.institutional_deaths = parse_integer(match.group(1))
            break
    
    for pattern in METRIC_PATTERNS['functional_ambulance']:
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            report.functional_ambulance = parse_integer(match.group(1))
            break


def parse_remaining_metrics(text: str, report: HealthReport):
    """Parse any remaining metrics from the full text"""
    
    # Look for "No history of travel"
    if re.search(r'no\s+history\s+of\s+travel', text, re.IGNORECASE):
        report.malaria_history_travel = "No"
    
    # Look for other patterns that might appear anywhere
    for metric, patterns in METRIC_PATTERNS.items():
        # Skip if already set
        if getattr(report, metric, None) not in [None, "", 0, "0/0"]:
            continue
            
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1)
                
                # Determine if it's a fraction or integer
                if '/' in value:
                    setattr(report, metric, parse_fraction(value))
                else:
                    setattr(report, metric, parse_integer(value))
                break


def parse_multiple_reports(text: str) -> List[HealthReport]:
    """
    Parse multiple facility reports from a single text file
    
    Useful for batch processing where multiple facilities are in one file
    """
    reports = []
    
    # Split by facility (look for patterns like "Matotwe rhc", "Maurice nyagumbo clinic")
    facility_pattern = r'(?=[A-Za-z\s]+(?:rhc|RHC|clinic|Clinic|hospital|Hospital)\s)'
    
    # Alternative: split by blank lines followed by facility name
    sections = re.split(r'\n\s*\n(?=[A-Za-z])', text)
    
    for section in sections:
        if not section.strip():
            continue
        
        # Check if this section contains a facility name
        if extract_facility_name(section):
            try:
                report = parse_health_report(section)
                reports.append(report)
                logger.info(f"Parsed report for {report.facility_name}")
            except Exception as e:
                logger.error(f"Error parsing section: {str(e)}")
    
    return reports


def validate_report(report: HealthReport) -> List[str]:
    """
    Validate a parsed report for data quality issues
    
    Returns list of warning messages
    """
    warnings = []
    
    # Check for missing week
    if report.week == 0:
        warnings.append("Week number not found")
    
    # Check for missing facility name
    if report.facility_name == "Unknown Facility":
        warnings.append("Facility name not found")
    
    # Check for zeros where we might expect values
    if report.opd_visits == 0:
        warnings.append("OPD visits reported as zero - please verify")
    
    if report.anc_contacts == 0 and report.institutional_deliveries > 0:
        warnings.append("Deliveries reported but no ANC contacts")
    
    if report.institutional_deliveries == 0 and report.still_births > 0:
        warnings.append("Still births reported but no deliveries")
    
    # Check malaria data consistency
    tested_num, tested_den = report.get_fraction_parts('malaria_tested')
    pos_num, pos_den = report.get_fraction_parts('malaria_positive')
    
    if tested_num > 0 and pos_num > tested_num:
        warnings.append("Malaria positives exceed tests performed")
    
    if tested_den > 0 and tested_num > tested_den:
        warnings.append("Malaria tests exceed suspected cases")
    
    # Check for missing sections
    if report.malaria_suspected == "0/0" and report.malaria_tested == "0/0":
        warnings.append("RDNS section may be missing or incomplete")
    
    return warnings


# ======================
# UTILITY FUNCTIONS
# ======================

def report_to_dataframe_row(report: HealthReport) -> Dict[str, Any]:
    """Convert report to a dictionary suitable for pandas DataFrame"""
    row = report.to_dict()
    
    # Add parsed fraction components
    for field in ['malaria_suspected', 'malaria_tested', 'malaria_positive', 
                  'diarrhoea', 'dysentery', 'influenza']:
        num, den = report.get_fraction_parts(field)
        row[f'{field}_numerator'] = num
        row[f'{field}_denominator'] = den
        if den > 0:
            row[f'{field}_rate'] = num / den
        else:
            row[f'{field}_rate'] = 0.0
    
    # Remove raw text to keep dataframe clean
    if 'raw_text' in row:
        del row['raw_text']
    
    return row


def format_report_preview(report: HealthReport) -> str:
    """Create a human-readable preview of the report"""
    lines = []
    lines.append("=" * 50)
    lines.append(f"Facility: {report.facility_name}")
    lines.append(f"Week: {report.week}, Year: {report.year}")
    lines.append("-" * 50)
    
    # Key metrics
    lines.append(f"OPD Visits: {report.opd_visits}")
    lines.append(f"Malaria: {report.malaria_suspected} suspected, {report.malaria_positive} positive")
    lines.append(f"Diarrhoea: {report.diarrhoea}")
    lines.append(f"Deliveries: {report.institutional_deliveries} institutional, {report.home_deliveries} home")
    lines.append(f"ANC Contacts: {report.anc_contacts}")
    lines.append(f"FP Clients: {report.fp_clients}")
    lines.append(f"HIV Tested: {report.hiv_tested}")
    
    return "\n".join(lines)


# ======================
# MAIN TEST FUNCTION
# ======================

if __name__ == "__main__":
    # Test with sample data
    sample_text = """
    Matotwe rhc
    Weekly  RDNS
    Wk 09
    Malaria suspected 0/0
    Tested 0/0
    Confirmed positive 0/0
    Diarrhoea 0/0
    Dysentery 0/0
    Influenza 0/0
    Maternal death 0
    Perinatal death 0 

    VHWs
    malaria suspected 0/0
    Malaria tested 0/0
    Malaria positive 0/0

    AEFI  0
    AFP 0
    NNT 0
    Measles 0

    OPD 
    Weekly delivery service 

    No of Drs who resigned= 0 no of nurses who resigned= 0
    No of pt who visited casualty= 0
    No of opd visits 41
    No of in patients admissions= 0
    No of major operations done =0
    No c/section done =0 
    No of renal dyalisis done= 0
    No of ANC contact =3
    No of clients who received FP  --7
    No of clients who attended PNC -3
    No of institutional deliveries  0
    No of home delivery 00
    No of still birth 0
    No of chn vaccinated penta 3.   0
    ÌNo of  under 5 s with SAM 00
    No of under 5 s with MAM 0
    No of tested for HIV  --2
    No of chn given vit A  -3
    No of Tb patients new and relapse 00
    No of institutionalb death 0
    No of functional ambulance 0
    """
    
    # Parse the report
    report = parse_health_report(sample_text)
    
    # Print preview
    print(format_report_preview(report))
    
    # Validate
    warnings = validate_report(report)
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")
    
    # Test multiple reports
    multiple = """
    Maurice nyagumbo clinic
    WEEK 9
    Rdns
    Suspected Mal~ 6/6
    Tested 6/6
    Positive 0/1
    
    Mayo 1 RHC 
    Wkly RDNS
    Wk 9
    Malaria suspected 4/15
    Tested 4/15
    Positive 0/10
    """
    
    reports = parse_multiple_reports(multiple)
    print(f"\nParsed {len(reports)} reports from multiple text")