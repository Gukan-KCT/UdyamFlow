const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

// Token and Role Storage Helpers
export function getActiveToken() {
  return localStorage.getItem("udyamflow_token") || "";
}

export function setActiveToken(token) {
  if (token) {
    localStorage.setItem("udyamflow_token", token);
  } else {
    localStorage.removeItem("udyamflow_token");
  }
}

export function getActiveUser() {
  const u = localStorage.getItem("udyamflow_user");
  try {
    return u ? JSON.parse(u) : null;
  } catch {
    return null;
  }
}

export function setActiveUser(user) {
  if (user) {
    localStorage.setItem("udyamflow_user", JSON.stringify(user));
  } else {
    localStorage.removeItem("udyamflow_user");
  }
}

function authHeaders(extraHeaders = {}) {
  const token = getActiveToken();
  const headers = { "Content-Type": "application/json", ...extraHeaders };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

// ----------------- AUTH -----------------
export async function login(email, password) {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Authentication failed");
  }
  const data = await res.json();
  setActiveToken(data.access_token);
  setActiveUser(data.user);
  return data;
}

export async function getCurrentUser() {
  const res = await fetch(`${BASE_URL}/auth/me`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch current user");
  return res.json();
}

export async function fetchDepartments() {
  const res = await fetch(`${BASE_URL}/auth/departments`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch departments");
  return res.json();
}

// ----------------- PROFILE -----------------
export async function fetchBusinessProfile() {
  const res = await fetch(`${BASE_URL}/profile`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch profile");
  return res.json();
}

export async function saveBusinessProfile(profileData) {
  const res = await fetch(`${BASE_URL}/profile`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(profileData),
  });
  if (!res.ok) throw new Error("Failed to save profile");
  return res.json();
}

export async function fetchVerifiedData() {
  const res = await fetch(`${BASE_URL}/profile/verified-data`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch verified data");
  return res.json();
}

// ----------------- REGULATORY CHECKLIST -----------------
export async function fetchChecklistSectors() {
  const res = await fetch(`${BASE_URL}/checklist/sectors`);
  if (!res.ok) throw new Error("Failed to fetch sectors");
  return res.json();
}

export async function fetchChecklistStages() {
  const res = await fetch(`${BASE_URL}/checklist/stages`);
  if (!res.ok) throw new Error("Failed to fetch stages");
  return res.json();
}

export async function fetchApprovalCatalogue(stage = null, sector = null) {
  let url = `${BASE_URL}/checklist/catalogue`;
  const params = [];
  if (stage) params.push(`stage=${encodeURIComponent(stage)}`);
  if (sector) params.push(`sector=${encodeURIComponent(sector)}`);
  if (params.length) url += `?${params.join("&")}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch catalogue");
  return res.json();
}

export async function generateChecklist(payload) {
  const res = await fetch(`${BASE_URL}/checklist/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to generate checklist");
  return res.json();
}

// ----------------- SINGLE-WINDOW APPLICATIONS -----------------
export async function fetchApplications(status = null) {
  const url = status ? `${BASE_URL}/applications?status=${status}` : `${BASE_URL}/applications`;
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch applications");
  return res.json();
}

export async function fetchApplicationDetails(applicationId) {
  const res = await fetch(`${BASE_URL}/applications/${applicationId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch application details");
  return res.json();
}

export async function createApplication(payload) {
  const res = await fetch(`${BASE_URL}/applications`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to submit application");
  }
  return res.json();
}

export async function executeApprovalAction(applicationId, appApprovalId, action, reason = null, nextStage = null) {
  const res = await fetch(`${BASE_URL}/applications/${applicationId}/approvals/${appApprovalId}/action`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ action, reason, next_stage: nextStage }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to execute approval action");
  }
  return res.json();
}

export async function fetchApplicationQueries(applicationId) {
  const res = await fetch(`${BASE_URL}/applications/${applicationId}/queries`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch queries");
  return res.json();
}

export async function raiseQuery(appApprovalId, queryText) {
  const res = await fetch(`${BASE_URL}/applications/queries`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ app_approval_id: appApprovalId, query_text: queryText }),
  });
  if (!res.ok) throw new Error("Failed to raise query");
  return res.json();
}

export async function respondToQuery(queryId, responseText, responseDocIds = []) {
  const res = await fetch(`${BASE_URL}/applications/queries/${queryId}/respond`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ response_text: responseText, response_doc_ids: responseDocIds }),
  });
  if (!res.ok) throw new Error("Failed to respond to query");
  return res.json();
}

// ----------------- DOCUMENTS & PRE-VALIDATION -----------------
export async function fetchDocumentVault() {
  const res = await fetch(`${BASE_URL}/documents/vault`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch document vault");
  return res.json();
}

export async function uploadDocument(payload) {
  const res = await fetch(`${BASE_URL}/documents/upload`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to upload document");
  return res.json();
}

export async function preValidateApplication(payload) {
  const res = await fetch(`${BASE_URL}/documents/pre-validate`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to pre-validate application");
  return res.json();
}

// ----------------- COMMON INSPECTIONS -----------------
export async function fetchInspections() {
  const res = await fetch(`${BASE_URL}/inspections`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch inspections");
  return res.json();
}

export async function scheduleCommonInspection(payload) {
  const res = await fetch(`${BASE_URL}/inspections/schedule`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to schedule inspection");
  return res.json();
}

export async function submitInspectionReport(inspectionId, payload) {
  const res = await fetch(`${BASE_URL}/inspections/${inspectionId}/report`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to submit inspection report");
  return res.json();
}

// ----------------- GRIEVANCES -----------------
export async function fetchGrievances() {
  const res = await fetch(`${BASE_URL}/grievances`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch grievances");
  return res.json();
}

export async function fileGrievance(payload) {
  const res = await fetch(`${BASE_URL}/grievances`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to file grievance");
  return res.json();
}

export async function escalateGrievance(grievanceId) {
  const res = await fetch(`${BASE_URL}/grievances/${grievanceId}/escalate`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to escalate grievance");
  return res.json();
}

export async function resolveGrievance(grievanceId, status, resolutionNotes) {
  const res = await fetch(`${BASE_URL}/grievances/${grievanceId}/resolve`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ status, resolution_notes: resolutionNotes }),
  });
  if (!res.ok) throw new Error("Failed to resolve grievance");
  return res.json();
}

// ----------------- DELAY ANALYTICS -----------------
export async function fetchDelayAnalytics() {
  const res = await fetch(`${BASE_URL}/delay-analytics/applications`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch delay analytics");
  return res.json();
}

export async function fetchDepartmentBottlenecks() {
  const res = await fetch(`${BASE_URL}/delay-analytics/bottlenecks`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch department bottlenecks");
  return res.json();
}

// ----------------- COMPLIANCE, RENEWALS & SCHEMES -----------------
export async function fetchComplianceTasks() {
  const res = await fetch(`${BASE_URL}/compliance/tasks`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch compliance tasks");
  return res.json();
}

export async function completeComplianceTask(taskId) {
  const res = await fetch(`${BASE_URL}/compliance/tasks/${taskId}/complete`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to complete task");
  return res.json();
}

export async function fetchRenewals() {
  const res = await fetch(`${BASE_URL}/compliance/renewals`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch renewals");
  return res.json();
}

export async function fetchCertificate(certificateId) {
  const res = await fetch(`${BASE_URL}/certificates/${certificateId}`);
  if (!res.ok) throw new Error("Failed to fetch certificate");
  return res.json();
}

export async function fetchApprovalCertificate(appApprovalId) {
  const res = await fetch(`${BASE_URL}/certificates/approval/${appApprovalId}`);
  if (!res.ok) throw new Error("Certificate not found for this approval");
  return res.json();
}

export async function verifyCertificatePublic(qrCode) {
  const res = await fetch(`${BASE_URL}/certificates/verify/${encodeURIComponent(qrCode)}`);
  if (!res.ok) throw new Error("Failed to verify certificate");
  return res.json();
}

export async function fetchSchemes() {
  const res = await fetch(`${BASE_URL}/schemes`);
  if (!res.ok) throw new Error("Failed to fetch schemes");
  return res.json();
}

export async function applyForScheme(payload) {
  const res = await fetch(`${BASE_URL}/schemes/apply`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to apply for scheme");
  return res.json();
}

export async function fetchMySchemeApplications() {
  const res = await fetch(`${BASE_URL}/schemes/my-applications`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch scheme applications");
  return res.json();
}

export async function fetchAuditLogs(filters = {}) {
  const params = new URLSearchParams();
  if (filters.action) params.append("action", filters.action);
  if (filters.actor_id) params.append("actor_id", filters.actor_id);
  if (filters.limit) params.append("limit", filters.limit);
  const res = await fetch(`${BASE_URL}/audit-logs?${params.toString()}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch audit logs");
  return res.json();
}

// ----------------- LEGACY RADAR -----------------
export async function fetchSummary() {
  const res = await fetch(`${BASE_URL}/dashboard/summary`);
  if (!res.ok) throw new Error("Failed to fetch summary");
  return res.json();
}

export async function fetchAlerts(type = "all") {
  const res = await fetch(`${BASE_URL}/alerts?type=${type}`);
  if (!res.ok) throw new Error("Failed to fetch alerts");
  return res.json();
}

export async function fetchDashboardCharts() {
  const res = await fetch(`${BASE_URL}/dashboard/charts`);
  if (!res.ok) throw new Error("Failed to fetch dashboard charts");
  return res.json();
}

export async function fetchOrgTree() {
  const res = await fetch(`${BASE_URL}/org/tree`);
  if (!res.ok) throw new Error("Failed to fetch org tree");
  return res.json();
}

export async function fetchFileJourney(fileId) {
  const res = await fetch(`${BASE_URL}/files/${fileId}/journey`);
  if (!res.ok) throw new Error("Failed to fetch file journey");
  return res.json();
}

export async function fetchEmployeeWorkload(employeeId) {
  const res = await fetch(`${BASE_URL}/employees/${employeeId}/workload`);
  if (!res.ok) throw new Error("Failed to fetch employee workload");
  return res.json();
}

export async function fetchAssistantResponse(message, active_file_id = null, active_employee_id = null) {
  const body = { message };
  if (active_file_id) body.active_file_id = active_file_id;
  if (active_employee_id) body.active_employee_id = active_employee_id;

  const res = await fetch(`${BASE_URL}/assistant/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("Failed to get assistant response");
  return res.json();
}
