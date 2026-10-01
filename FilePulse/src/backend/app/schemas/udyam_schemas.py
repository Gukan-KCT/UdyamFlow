from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

# User & Auth
UserRole = Literal["applicant", "dept_officer", "senior_officer", "nodal_officer", "admin"]

class UserRegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: str
    phone: str | None = None
    role: UserRole = "applicant"
    department_id: str | None = None

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    phone: str | None = None
    role: str
    department_id: str | None = None
    is_active: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Business Profile
class BusinessProfileCreate(BaseModel):
    enterprise_name: str
    entity_type: str = "Pvt Ltd"
    udyam_registration: str | None = None
    pan: str
    gstin: str | None = None
    sector: str = "Manufacturing"
    project_size: str = "Small"
    investment_cr: float
    turnover_cr: float
    location_type: str = "Industrial Area"
    district: str
    state: str = "Maharashtra"
    address: str
    lat: float | None = None
    lng: float | None = None

class BusinessProfileResponse(BusinessProfileCreate):
    profile_id: str
    user_id: str
    created_at: str
    updated_at: str

# Checklist & Approvals Catalogue
class ChecklistRequest(BaseModel):
    sector: str = "Manufacturing"
    stage: str = "Pre-Establishment" # Pre-Establishment, Pre-Operation, Renewal
    project_size: str = "Small" # Micro, Small, Medium, Large
    location_type: str = "Industrial Area" # Industrial Area, Municipal / Urban, Rural / Panchayat, Eco-sensitive Zone
    investment_cr: float = 5.0
    turnover_cr: float = 15.0

class ApprovalItemResponse(BaseModel):
    approval_id: str
    name: str
    department_id: str
    department_name: str | None = None
    sector: str
    stage: str
    project_size: str
    location_type: str
    statutory_act: str
    max_sla_days: int
    fee_inr: float
    prerequisites: list[str] = []
    documents_required: list[str] = []
    validity_years: int
    sample_disclaimer: str

class ChecklistResponse(BaseModel):
    matched_approvals: list[ApprovalItemResponse]
    total_approvals: int
    estimated_total_fee: float
    critical_path_sla_days: int
    sector: str
    stage: str
    project_size: str
    location_type: str
    sample_disclaimer: str

# Single Window Application
class ApplicationCreate(BaseModel):
    profile_id: str
    approval_ids: list[str]
    remarks: str | None = None

class ApplicationApprovalResponse(BaseModel):
    app_approval_id: str
    application_id: str
    approval_id: str
    approval_name: str
    department_id: str
    department_name: str
    status: str
    assigned_officer_id: str | None = None
    assigned_officer_name: str | None = None
    current_stage: str
    sla_days: int
    deadline_at: str | None = None
    fee_paid: float
    risk_score: int
    days_inactive: int
    query_count: int
    loop_count: int
    rejection_reason: str | None = None
    approved_at: str | None = None

class ApplicationResponse(BaseModel):
    application_id: str
    application_number: str
    user_id: str
    profile_id: str
    enterprise_name: str | None = None
    status: str
    submitted_at: str | None = None
    target_completion_at: str | None = None
    completed_at: str | None = None
    total_fee: float
    overall_sla_days: int
    remarks: str | None = None
    approvals: list[ApplicationApprovalResponse] = []
    created_at: str
    updated_at: str

class ApplicationApprovalActionRequest(BaseModel):
    action: Literal["APPROVE", "REJECT", "ASSIGN", "MOVE_STAGE"]
    reason: str | None = None
    assigned_officer_id: str | None = None
    next_stage: str | None = None

# Documents & Pre-Validation
class DocumentUploadRequest(BaseModel):
    doc_type: str
    title: str
    file_name: str
    file_size: int
    mime_type: str
    storage_path: str = "/storage/docs/sample.pdf"
    hash_sha256: str = "sample_sha256_hash"
    profile_id: str | None = None
    expires_at: str | None = None

class DocumentResponse(BaseModel):
    document_id: str
    user_id: str
    profile_id: str | None = None
    doc_type: str
    title: str
    file_name: str
    file_size: int
    mime_type: str
    storage_path: str
    hash_sha256: str
    verified: bool
    verified_at: str | None = None
    expires_at: str | None = None
    created_at: str

class PreValidateRequest(BaseModel):
    approval_ids: list[str]
    uploaded_doc_types: list[str]
    form_data: dict[str, Any] = {}

class DocumentValidationItem(BaseModel):
    doc_type: str
    name: str
    status: Literal["VALID", "MISSING", "EXPIRED", "FORMAT_ERROR"]
    message: str

class PreValidateResponse(BaseModel):
    is_valid: bool
    score: int # 0 to 100
    validations: list[DocumentValidationItem]
    missing_required_docs: list[str]
    autofill_suggestions: dict[str, str] = {}
    readiness_summary: str

# Queries
class QueryCreateRequest(BaseModel):
    app_approval_id: str
    query_text: str

class QueryRespondRequest(BaseModel):
    response_text: str
    response_doc_ids: list[str] = []

class QueryResponse(BaseModel):
    query_id: str
    app_approval_id: str
    department_id: str
    department_name: str | None = None
    officer_id: str
    officer_name: str | None = None
    query_text: str
    status: str
    raised_at: str
    responded_at: str | None = None
    response_text: str | None = None
    response_doc_ids: list[str] = []

# Inspections
class InspectionScheduleRequest(BaseModel):
    application_id: str
    scheduled_date: str # YYYY-MM-DD
    time_slot: str # Morning (10:00 - 13:00) or Afternoon (14:00 - 17:00)
    departments: list[str]
    notes: str | None = None

class InspectionReportSubmitRequest(BaseModel):
    verdict: Literal["SATISFACTORY", "CONDITIONAL", "UNSATISFACTORY"]
    report_text: str
    findings: list[str] = []

class InspectionResponse(BaseModel):
    inspection_id: str
    application_id: str
    enterprise_name: str | None = None
    scheduled_date: str
    time_slot: str
    status: str
    departments: list[str]
    officers: list[str]
    notes: str | None = None
    verdict: str | None = None
    report_text: str | None = None
    findings: list[str] = []
    completed_at: str | None = None
    created_at: str

# Grievances
class GrievanceCreateRequest(BaseModel):
    application_id: str | None = None
    department_id: str
    category: str
    subject: str
    description: str

class GrievanceResolveRequest(BaseModel):
    status: Literal["RESOLVED", "CLOSED", "ESCALATED"]
    resolution_notes: str

class GrievanceResponse(BaseModel):
    grievance_id: str
    grievance_number: str
    user_id: str
    application_id: str | None = None
    department_id: str
    department_name: str | None = None
    category: str
    subject: str
    description: str
    level: int
    status: str
    assigned_to: str | None = None
    filed_at: str
    deadline_at: str
    resolved_at: str | None = None
    resolution_notes: str | None = None
    escalated_at: str | None = None

# Certificates, Renewals, Compliance
class CertificateResponse(BaseModel):
    certificate_id: str
    app_approval_id: str
    certificate_number: str
    approval_name: str
    department_name: str
    issued_to: str
    enterprise_name: str
    issue_date: str
    valid_until: str
    qr_verification_code: str
    digital_signature_hash: str
    status: str
    pdf_url: str | None = None

class ComplianceTaskResponse(BaseModel):
    task_id: str
    user_id: str
    enterprise_name: str
    title: str
    category: str
    department_name: str
    due_date: str
    status: str
    recurring_period: str
    statutory_ref: str
    completed_at: str | None = None

class RenewalResponse(BaseModel):
    renewal_id: str
    certificate_id: str
    certificate_number: str
    approval_name: str
    current_expiry: str
    reminder_days: int
    renewal_status: str
    renewal_application_id: str | None = None

# Schemes
class SchemeResponse(BaseModel):
    scheme_id: str
    name: str
    department_name: str
    eligible_sectors: list[str]
    eligible_sizes: list[str]
    incentive_type: str
    benefit_details: str
    eligibility_criteria: str
    max_subsidy_inr: float
    application_deadline: str | None = None
    sample_disclaimer: str

class SchemeApplicationRequest(BaseModel):
    scheme_id: str
    profile_id: str
    claim_amount: float
    remarks: str | None = None

class SchemeApplicationResponse(BaseModel):
    scheme_app_id: str
    scheme_id: str
    scheme_name: str
    user_id: str
    enterprise_name: str
    status: str
    claim_amount: float
    approved_amount: float
    submitted_at: str
    reviewed_at: str | None = None
    remarks: str | None = None

# Audit Log
class AuditLogResponse(BaseModel):
    audit_id: str
    actor_id: str
    actor_role: str
    action: str
    entity_type: str
    entity_id: str
    before_state: dict[str, Any] | None = None
    after_state: dict[str, Any] | None = None
    reason: str | None = None
    ip_address: str | None = None
    timestamp: str

# Notifications
class NotificationResponse(BaseModel):
    notification_id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    link_url: str | None = None
    created_at: str
