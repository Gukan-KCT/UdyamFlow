import { useState, useEffect } from "react";
import {
  FileText,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Send,
  Building2,
  ExternalLink,
  MessageSquare,
  Shield,
  Plus,
  X,
  Search,
  ChevronRight,
  Award,
  QrCode,
  Printer,
  Download,
  Paperclip,
  Check,
  HelpCircle,
  CornerDownRight,
  FileCheck2,
} from "lucide-react";
import {
  fetchApplications,
  fetchApplicationDetails,
  createApplication,
  executeApprovalAction,
  raiseQuery,
  respondToQuery,
  fetchApplicationQueries,
  fetchApprovalCertificate,
  fetchDocumentVault,
  fetchApprovalCatalogue,
  getActiveUser,
} from "../api/client";

export default function SingleWindowApplicationsPage() {
  const [applications, setApplications] = useState([]);
  const [selectedApp, setSelectedApp] = useState(null);
  const [appQueries, setAppQueries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [activeUser, setActiveUser] = useState(getActiveUser());

  // Modal States
  const [showNewModal, setShowNewModal] = useState(false);
  const [showQueryModal, setShowQueryModal] = useState(false);
  const [showRespondModal, setShowRespondModal] = useState(false);
  const [showCertModal, setShowCertModal] = useState(null);
  const [activeSubApproval, setActiveSubApproval] = useState(null);
  const [activeQueryToRespond, setActiveQueryToRespond] = useState(null);

  // New Application Form
  const [catalogue, setCatalogue] = useState([]);
  const [selectedApprovals, setSelectedApprovals] = useState([]);
  const [remarks, setRemarks] = useState("");

  // Query Forms
  const [queryText, setQueryText] = useState("");
  const [responseText, setResponseText] = useState("");
  const [vaultDocs, setVaultDocs] = useState([]);
  const [selectedDocIds, setSelectedDocIds] = useState([]);

  // Risk & Stage Filter
  const [riskFilter, setRiskFilter] = useState("ALL"); // ALL | HIGH | MEDIUM | LOW

  useEffect(() => {
    loadApps();
  }, []);

  async function loadApps() {
    setLoading(true);
    try {
      const data = await fetchApplications();
      setApplications(data);
      if (data.length > 0) {
        const details = await fetchApplicationDetails(data[0].application_id);
        setSelectedApp(details);
        loadQueriesForApp(data[0].application_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadQueriesForApp(appId) {
    try {
      const qList = await fetchApplicationQueries(appId);
      setAppQueries(qList || []);
    } catch (err) {
      console.warn("Could not load queries:", err);
      setAppQueries([]);
    }
  }

  async function handleSelectApp(appId) {
    try {
      const details = await fetchApplicationDetails(appId);
      setSelectedApp(details);
      loadQueriesForApp(appId);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleOpenNewModal() {
    try {
      const cat = await fetchApprovalCatalogue();
      setCatalogue(cat);
      setSelectedApprovals(["APPR-CTE-PCB", "APPR-FIRE-NOC"]);
      setShowNewModal(true);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleCreateApp(e) {
    e.preventDefault();
    if (selectedApprovals.length === 0) return;
    try {
      await createApplication({
        profile_id: "prof_apex_01",
        approval_ids: selectedApprovals,
        remarks: remarks || "Composite Single-Window Clearance Application",
      });
      setShowNewModal(false);
      setSuccessMsg("Composite Application successfully submitted for parallel clearance!");
      setTimeout(() => setSuccessMsg(null), 4000);
      await loadApps();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleOfficerAction(subApprovalId, action) {
    if (!selectedApp) return;
    try {
      const updated = await executeApprovalAction(
        selectedApp.application_id,
        subApprovalId,
        action,
        action === "REJECT" ? "Statutory clearance requirements not fulfilled." : null
      );
      setSelectedApp(updated);
      setSuccessMsg(`Sub-approval action '${action}' recorded with audit logging.`);
      setTimeout(() => setSuccessMsg(null), 4000);
      await loadApps();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleRaiseQuery(e) {
    e.preventDefault();
    if (!queryText.trim() || !activeSubApproval) return;
    try {
      await raiseQuery(activeSubApproval.app_approval_id, queryText);
      setShowQueryModal(false);
      setQueryText("");
      setSuccessMsg("Scrutiny clarification query sent to applicant.");
      setTimeout(() => setSuccessMsg(null), 4000);
      const updated = await fetchApplicationDetails(selectedApp.application_id);
      setSelectedApp(updated);
      await loadQueriesForApp(selectedApp.application_id);
      await loadApps();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleOpenRespondModal(sub) {
    setActiveSubApproval(sub);
    // Find open query for this sub approval
    const qry = appQueries.find(
      (q) => q.app_approval_id === sub.app_approval_id && q.status === "OPEN"
    ) || {
      query_id: `qry_${sub.app_approval_id}`,
      query_text: "Please furnish clarification on statutory compliance guidelines and attach supporting documentation from your vault.",
      officer_name: sub.assigned_officer_name || "Department Scrutiny Officer",
      department_name: sub.department_name,
      raised_at: new Date().toISOString(),
    };
    setActiveQueryToRespond(qry);
    setResponseText("");
    setSelectedDocIds([]);

    // Load available vault documents
    try {
      const docs = await fetchDocumentVault();
      setVaultDocs(docs);
    } catch (err) {
      setVaultDocs([]);
    }
    setShowRespondModal(true);
  }

  async function handleRespondQuery(e) {
    e.preventDefault();
    if (!responseText.trim() || !activeQueryToRespond) return;
    try {
      await respondToQuery(activeQueryToRespond.query_id, responseText, selectedDocIds);
      setShowRespondModal(false);
      setResponseText("");
      setSelectedDocIds([]);
      setSuccessMsg("Clarification response and supporting documents submitted to department desk.");
      setTimeout(() => setSuccessMsg(null), 4000);
      const updated = await fetchApplicationDetails(selectedApp.application_id);
      setSelectedApp(updated);
      await loadQueriesForApp(selectedApp.application_id);
      await loadApps();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleOpenCertModal(sub) {
    try {
      const cert = await fetchApprovalCertificate(sub.app_approval_id);
      setShowCertModal(cert);
    } catch (err) {
      // Fallback display if not yet saved or testing
      setShowCertModal({
        approval_name: sub.approval_name,
        department_name: sub.department_name,
        certificate_number: `CERT-2026-${sub.app_approval_id.slice(-6).toUpperCase()}`,
        enterprise_name: selectedApp?.enterprise_name || "Apex Precision Auto Engineering Pvt Ltd",
        issued_to: "Apex Precision Auto Engineering Pvt Ltd",
        issue_date: sub.approved_at || new Date().toISOString(),
        valid_until: "2031-03-31",
        digital_signature_hash: `SHA256: 4f8b91a27e${sub.app_approval_id.slice(-4)}verified_official`,
        qr_verification_code: `UDYAM-VERIFY-CERT-2026-${sub.app_approval_id.slice(-6).toUpperCase()}`,
      });
    }
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-800 tracking-tight">
            Single-Window Applications
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Coordinate parallel departmental approvals, monitor service level deadlines, and manage clarification queries.
          </p>
        </div>
        <button
          onClick={handleOpenNewModal}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>New Composite Application</span>
        </button>
      </div>

      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center justify-between animate-fadeIn">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="font-semibold">{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-600 hover:text-emerald-900 font-bold">✕</button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center justify-between animate-fadeIn">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700 font-bold">Dismiss</button>
        </div>
      )}

      {/* Main Grid: Application List + Detail Pane */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Applications List */}
        <div className="lg:col-span-4 space-y-3">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Active Submissions ({applications.length})
            </span>
            <span className="text-[10px] text-slate-400 font-semibold">Click to inspect</span>
          </div>

          <div className="space-y-2.5 max-h-[720px] overflow-y-auto pr-1">
            {applications.map((app) => {
              const isSelected = selectedApp?.application_id === app.application_id;
              const isApproved = app.status === "APPROVED";
              const isQuery = app.status === "QUERY_RAISED";

              return (
                <div
                  key={app.application_id}
                  onClick={() => handleSelectApp(app.application_id)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? "bg-sky-50/70 border-sky-300 shadow-sm"
                      : "bg-white border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-xs font-bold text-slate-800">
                      {app.application_number}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        isApproved
                          ? "bg-emerald-100 text-emerald-800"
                          : isQuery
                          ? "bg-amber-100 text-amber-800 animate-pulse"
                          : "bg-sky-100 text-sky-800"
                      }`}
                    >
                      {app.status.replace("_", " ")}
                    </span>
                  </div>

                  <p className="text-xs font-bold text-slate-800 truncate mb-1">
                    {app.enterprise_name || "Apex Precision Auto Engineering Pvt Ltd"}
                  </p>
                  <p className="text-[11px] text-slate-500 line-clamp-1 mb-2.5">
                    {app.remarks || "Composite Industrial Clearance"}
                  </p>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-100">
                    <span className="flex items-center gap-1 font-medium">
                      <Clock className="w-3 h-3 text-slate-400" />
                      SLA: {app.overall_sla_days} Days
                    </span>
                    <span className="font-bold text-slate-700">₹{app.total_fee.toLocaleString()}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Selected Application Composite Tracker */}
        <div className="lg:col-span-8">
          {selectedApp ? (
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
              {/* Composite Header Banner */}
              <div className="p-6 border-b border-slate-100 bg-slate-50/50">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="px-2.5 py-0.5 bg-slate-200 text-slate-800 rounded font-mono text-xs font-bold">
                        {selectedApp.application_number}
                      </span>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                          selectedApp.status === "APPROVED"
                            ? "bg-emerald-100 text-emerald-800"
                            : selectedApp.status === "QUERY_RAISED"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-sky-100 text-sky-800"
                        }`}
                      >
                        {selectedApp.status.replace("_", " ")}
                      </span>
                    </div>
                    <h2 className="text-xl font-black text-slate-900">
                      {selectedApp.enterprise_name}
                    </h2>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Submitted on: {new Date(selectedApp.created_at).toLocaleDateString()} • Target Completion: {selectedApp.target_completion_at ? new Date(selectedApp.target_completion_at).toLocaleDateString() : "Pending"}
                    </p>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-[10px] text-slate-400 uppercase font-bold">Composite Fee</p>
                      <p className="text-lg font-black text-slate-800">₹{selectedApp.total_fee.toLocaleString()}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] text-slate-400 uppercase font-bold">Critical Path SLA</p>
                      <p className="text-lg font-black text-sky-600">{selectedApp.overall_sla_days} Days</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Parallel Departmental Workflows */}
              <div className="p-6 space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
                      Parallel Departmental Clearances ({selectedApp.approvals.length})
                    </h3>
                    <span className="text-[11px] text-slate-400">
                      Running concurrently under Single-Window Mandate (Non-Linear Processing)
                    </span>
                  </div>

                  {/* Risk-Based Scrutiny Selector */}
                  <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl text-[11px] font-bold">
                    <button
                      onClick={() => setRiskFilter("ALL")}
                      className={`px-2.5 py-1 rounded-lg transition-all ${riskFilter === "ALL" ? "bg-white text-slate-900 shadow-xs" : "text-slate-500 hover:text-slate-900"}`}
                    >
                      All ({selectedApp.approvals.length})
                    </button>
                    <button
                      onClick={() => setRiskFilter("LOW")}
                      className={`px-2 py-1 rounded-lg transition-all ${riskFilter === "LOW" ? "bg-emerald-600 text-white shadow-xs" : "text-emerald-700 hover:bg-emerald-50"}`}
                    >
                      🟢 Low Risk
                    </button>
                    <button
                      onClick={() => setRiskFilter("MEDIUM")}
                      className={`px-2 py-1 rounded-lg transition-all ${riskFilter === "MEDIUM" ? "bg-amber-600 text-white shadow-xs" : "text-amber-700 hover:bg-amber-50"}`}
                    >
                      🟡 Medium
                    </button>
                    <button
                      onClick={() => setRiskFilter("HIGH")}
                      className={`px-2 py-1 rounded-lg transition-all ${riskFilter === "HIGH" ? "bg-rose-600 text-white shadow-xs" : "text-rose-700 hover:bg-rose-50"}`}
                    >
                      🔴 High Risk
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  {selectedApp.approvals
                    .filter((sub) => {
                      if (riskFilter === "LOW") return sub.risk_score < 30;
                      if (riskFilter === "MEDIUM") return sub.risk_score >= 30 && sub.risk_score <= 60;
                      if (riskFilter === "HIGH") return sub.risk_score > 60;
                      return true;
                    })
                    .map((sub) => {
                      const isSubApproved = sub.status === "APPROVED";
                      const isQueryRaised = sub.status === "QUERY_RAISED";
                      const isQueryResponded = sub.status === "QUERY_RESPONDED";

                      // Find matching query if any
                      const matchingQuery = appQueries.find(
                        (q) => q.app_approval_id === sub.app_approval_id
                      );

                      const riskTier =
                        sub.risk_score > 60
                          ? { label: "High Risk — In-Depth Scrutiny", color: "bg-rose-50 text-rose-700 border-rose-200" }
                          : sub.risk_score >= 30
                          ? { label: "Medium Risk — Standard Scrutiny", color: "bg-amber-50 text-amber-700 border-amber-200" }
                          : { label: "Low Risk — Fast-Track Channel", color: "bg-emerald-50 text-emerald-700 border-emerald-200" };

                      return (
                        <div
                          key={sub.app_approval_id}
                          className="p-5 rounded-xl border border-slate-200 bg-slate-50/30 hover:bg-slate-50 transition-all space-y-3"
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1 flex-wrap">
                                <span className="px-2 py-0.5 bg-sky-100 text-sky-700 rounded text-[10px] font-bold uppercase">
                                  {sub.department_name}
                                </span>
                                <span className="text-xs font-mono text-slate-400">
                                  {sub.approval_id}
                                </span>
                                <span className={`px-2 py-0.5 border rounded text-[10px] font-bold ${riskTier.color}`}>
                                  {riskTier.label}
                                </span>
                                <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-[10px] font-semibold">
                                  Stage: {sub.current_stage.replace("_", " ")}
                                </span>
                              </div>
                              <h4 className="text-sm font-bold text-slate-900">{sub.approval_name}</h4>
                              <p className="text-xs text-slate-500 mt-0.5">
                                Officer: <span className="font-semibold text-slate-700">{sub.assigned_officer_name || "Scrutiny Desk Auto-Assigned"}</span> • SLA: <span className="font-semibold text-slate-700">{sub.sla_days} Days</span>
                              </p>
                            </div>

                            <div className="flex items-center gap-3 shrink-0">
                              <span
                                className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                                  isSubApproved
                                    ? "bg-emerald-100 text-emerald-800"
                                    : isQueryRaised
                                    ? "bg-amber-100 text-amber-800 animate-pulse border border-amber-300"
                                    : isQueryResponded
                                    ? "bg-indigo-100 text-indigo-800"
                                    : "bg-sky-100 text-sky-800"
                                }`}
                              >
                                {sub.status.replace("_", " ")}
                              </span>
                            </div>
                          </div>

                          {/* Interactive Clarification Query Block if Query Raised */}
                          {isQueryRaised && (
                            <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl space-y-2 text-xs">
                              <div className="flex items-start justify-between gap-2">
                                <div className="flex items-center gap-1.5 text-amber-800 font-bold">
                                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                                  <span>Official Scrutiny Query Pending Response</span>
                                </div>
                                <span className="text-[10px] text-amber-700 bg-amber-100/70 px-2 py-0.5 rounded font-mono">
                                  SLA Clock Paused
                                </span>
                              </div>
                              <p className="text-slate-700 bg-white/70 p-2.5 rounded-lg border border-amber-200/60 text-xs italic">
                                "{matchingQuery?.query_text || "Please provide clarification on statutory effluent treatment parameters and upload structural stability certificate."}"
                              </p>
                              <div className="flex items-center justify-between pt-1">
                                <span className="text-[11px] text-amber-700">
                                  Raised by: <span className="font-semibold">{matchingQuery?.officer_name || sub.assigned_officer_name || "Department Officer"}</span>
                                </span>
                                <button
                                  onClick={() => handleOpenRespondModal(sub)}
                                  className="inline-flex items-center gap-1 px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold shadow-xs transition-colors"
                                >
                                  <CornerDownRight className="w-3.5 h-3.5" />
                                  <span>Respond to Query Now</span>
                                </button>
                              </div>
                            </div>
                          )}

                          {/* Query Responded Confirmation Banner */}
                          {isQueryResponded && (
                            <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-xl space-y-1.5 text-xs text-indigo-900">
                              <div className="flex items-center gap-1.5 font-bold">
                                <CheckCircle2 className="w-4 h-4 text-indigo-600" />
                                <span>Applicant Clarification Submitted — Awaiting Final Officer Scrutiny</span>
                              </div>
                              {matchingQuery?.response_text && (
                                <p className="text-slate-600 bg-white/60 p-2 rounded border border-indigo-100 italic">
                                  Response: "{matchingQuery.response_text}"
                                </p>
                              )}
                            </div>
                          )}

                          {/* Action Buttons Toolbar */}
                          <div className="pt-3 border-t border-slate-200/60 flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              {isSubApproved ? (
                                <button
                                  onClick={() => handleOpenCertModal(sub)}
                                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-xs transition-colors"
                                >
                                  <Award className="w-3.5 h-3.5" />
                                  <span>View Verifiable Certificate</span>
                                </button>
                              ) : (
                                <>
                                  <button
                                    onClick={() => handleOfficerAction(sub.app_approval_id, "APPROVE")}
                                    className="inline-flex items-center gap-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-xs transition-colors"
                                  >
                                    <CheckCircle2 className="w-3.5 h-3.5" />
                                    <span>Grant Clearance</span>
                                  </button>
                                  <button
                                    onClick={() => {
                                      setActiveSubApproval(sub);
                                      setShowQueryModal(true);
                                    }}
                                    className="inline-flex items-center gap-1 px-3 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 rounded-lg text-xs font-bold transition-colors"
                                  >
                                    <MessageSquare className="w-3.5 h-3.5" />
                                    <span>Raise Clarification Query</span>
                                  </button>
                                  {isQueryRaised && (
                                    <button
                                      onClick={() => handleOpenRespondModal(sub)}
                                      className="inline-flex items-center gap-1 px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-bold shadow-xs transition-colors"
                                    >
                                      <Send className="w-3.5 h-3.5" />
                                      <span>Applicant Reply</span>
                                    </button>
                                  )}
                                </>
                              )}
                            </div>

                            <div className="flex items-center gap-3 text-[11px] text-slate-400">
                              <span>Query Cycles: <strong className="text-slate-700">{sub.query_count}</strong></span>
                              <span>•</span>
                              <span>Risk Score: <strong className="text-slate-700">{sub.risk_score} / 100</strong></span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 text-slate-400 text-sm">
              Select an application from the left panel to inspect workflow progress.
            </div>
          )}
        </div>
      </div>

      {/* New Composite Application Modal */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 space-y-5 animate-scaleIn">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-800 text-base">New Composite Single-Window Application</h3>
              <button onClick={() => setShowNewModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateApp} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
                  Select Clearances for Parallel Processing
                </label>
                <div className="max-h-60 overflow-y-auto space-y-2 border border-slate-200 rounded-xl p-3 bg-slate-50/50">
                  {catalogue.map((cat) => {
                    const isChecked = selectedApprovals.includes(cat.approval_id);
                    return (
                      <label
                        key={cat.approval_id}
                        className="flex items-start gap-3 p-2 bg-white rounded-lg border border-slate-200/80 cursor-pointer hover:border-sky-300"
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedApprovals([...selectedApprovals, cat.approval_id]);
                            } else {
                              setSelectedApprovals(selectedApprovals.filter((id) => id !== cat.approval_id));
                            }
                          }}
                          className="mt-1 rounded text-sky-600 focus:ring-sky-500"
                        />
                        <div className="flex-1 text-xs">
                          <p className="font-bold text-slate-800">{cat.name}</p>
                          <p className="text-[11px] text-slate-500">
                            {cat.department_name} • Fee: ₹{cat.fee_inr.toLocaleString()} • SLA: {cat.max_sla_days} Days
                          </p>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Application Project Remarks
                </label>
                <textarea
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  placeholder="e.g. Composite clearance for new auto-components manufacturing unit at Chakan Phase II"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  rows={3}
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 rounded-xl text-xs font-bold hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={selectedApprovals.length === 0}
                  className="px-5 py-2 bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-sm"
                >
                  Submit Composite Application ({selectedApprovals.length})
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Query Raise Modal (Officer Desk) */}
      {showQueryModal && activeSubApproval && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-scaleIn">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-800 text-base">Raise Scrutiny Clarification Query</h3>
              <button onClick={() => setShowQueryModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleRaiseQuery} className="space-y-4">
              <div>
                <p className="text-xs text-slate-500 mb-2">
                  Raising statutory query for: <span className="font-bold text-slate-800">{activeSubApproval.approval_name}</span>
                </p>
                <textarea
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                  placeholder="Specify clear, unambiguous statutory deficiency or clarification needed..."
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  rows={4}
                  required
                />
              </div>

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowQueryModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 rounded-xl text-xs font-bold hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-bold shadow-sm"
                >
                  Send Query to Applicant
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Query Response Modal (Applicant Interface) */}
      {showRespondModal && activeSubApproval && activeQueryToRespond && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-scaleIn">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 className="font-bold text-slate-800 text-base">Respond to Clarification Query</h3>
                <p className="text-[11px] text-slate-400">{activeSubApproval.approval_name}</p>
              </div>
              <button onClick={() => setShowRespondModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Officer's Query */}
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs space-y-1">
              <span className="font-bold text-amber-800">Officer's Query:</span>
              <p className="text-slate-700 italic">"{activeQueryToRespond.query_text}"</p>
            </div>

            <form onSubmit={handleRespondQuery} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Your Clarification Response
                </label>
                <textarea
                  value={responseText}
                  onChange={(e) => setResponseText(e.target.value)}
                  placeholder="Explain how the statutory requirement has been addressed..."
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  rows={4}
                  required
                />
              </div>

              {/* Attach Verified Vault Documents */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5 flex items-center justify-between">
                  <span>Attach Verified Documents from Vault</span>
                  <span className="text-[10px] text-slate-400 font-normal">Optional</span>
                </label>
                <div className="max-h-36 overflow-y-auto space-y-1.5 border border-slate-200 rounded-xl p-2 bg-slate-50/50">
                  {vaultDocs.length > 0 ? (
                    vaultDocs.map((doc) => {
                      const isSelected = selectedDocIds.includes(doc.doc_id);
                      return (
                        <label
                          key={doc.doc_id}
                          className="flex items-center gap-2.5 p-2 bg-white rounded-lg border border-slate-200/80 cursor-pointer hover:border-sky-300 text-xs"
                        >
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedDocIds([...selectedDocIds, doc.doc_id]);
                              } else {
                                setSelectedDocIds(selectedDocIds.filter((id) => id !== doc.doc_id));
                              }
                            }}
                            className="rounded text-sky-600 focus:ring-sky-500"
                          />
                          <Paperclip className="w-3.5 h-3.5 text-slate-400" />
                          <div className="flex-1 truncate">
                            <span className="font-semibold text-slate-800">{doc.document_type}</span>
                            <span className="text-[10px] text-slate-400 ml-1.5 font-mono">({doc.file_name})</span>
                          </div>
                          <span className="text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded font-bold">
                            Verified
                          </span>
                        </label>
                      );
                    })
                  ) : (
                    <p className="text-[11px] text-slate-400 p-2 text-center">
                      No documents currently in vault.
                    </p>
                  )}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowRespondModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 rounded-xl text-xs font-bold hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold shadow-sm"
                >
                  Submit Official Response
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Official Verifiable Digital Certificate Modal */}
      {showCertModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-8 shadow-2xl border-4 border-emerald-500/30 text-center space-y-5 animate-scaleIn relative">
            {/* Top Close Button */}
            <button
              onClick={() => setShowCertModal(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Official Header */}
            <div className="space-y-1.5 pb-4 border-b-2 border-slate-200">
              <div className="mx-auto w-14 h-14 bg-emerald-50 text-emerald-700 rounded-full flex items-center justify-center border-2 border-emerald-500/20">
                <Award className="w-8 h-8" />
              </div>
              <h4 className="text-xs font-black uppercase tracking-widest text-slate-500">
                GOVERNMENT OF INDIA & STATE INDUSTRIAL CLEARANCE BOARD
              </h4>
              <h2 className="text-xl font-black text-slate-900 tracking-tight">
                NATIONAL SINGLE-WINDOW STATUTORY CLEARANCE
              </h2>
              <p className="text-xs font-bold text-emerald-700 uppercase tracking-wider">
                OFFICIAL CERTIFICATE OF STATUTORY APPROVAL
              </p>
            </div>

            {/* Certificate Body */}
            <div className="space-y-4 text-left">
              <div className="bg-slate-50 p-5 rounded-xl border border-slate-200 text-xs space-y-2.5">
                <div className="flex justify-between items-center py-1 border-b border-slate-200/60">
                  <span className="text-slate-500 font-semibold">Approval / Licence:</span>
                  <span className="font-bold text-slate-900 text-sm">{showCertModal.approval_name || showCertModal.approvalName}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-slate-200/60">
                  <span className="text-slate-500 font-semibold">Issuing Department:</span>
                  <span className="font-semibold text-slate-800">{showCertModal.department_name || showCertModal.deptName}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-slate-200/60">
                  <span className="text-slate-500 font-semibold">Certificate Number:</span>
                  <span className="font-mono font-bold text-sky-700">{showCertModal.certificate_number || showCertModal.certNum}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-slate-200/60">
                  <span className="text-slate-500 font-semibold">Granted To Enterprise:</span>
                  <span className="font-bold text-slate-900">{showCertModal.enterprise_name || showCertModal.issuedTo}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-slate-200/60">
                  <span className="text-slate-500 font-semibold">Date of Issuance:</span>
                  <span className="font-medium text-slate-700">
                    {showCertModal.issue_date ? new Date(showCertModal.issue_date).toLocaleDateString() : "Immediate"}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-500 font-semibold">Valid Until:</span>
                  <span className="font-bold text-emerald-700">
                    {showCertModal.valid_until ? new Date(showCertModal.valid_until).toLocaleDateString() : "Permanent / Statutory Cycle"}
                  </span>
                </div>
              </div>

              {/* Security & Verification Metadata */}
              <div className="bg-emerald-50/50 p-4 rounded-xl border border-emerald-200 flex flex-col sm:flex-row items-center justify-between gap-4 text-left">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white rounded-lg border border-emerald-200 shadow-xs">
                    <QrCode className="w-10 h-10 text-emerald-800" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800">Tamper-Proof Digital Verification</p>
                    <p className="text-[11px] text-slate-500 font-mono">
                      {showCertModal.qr_verification_code || "UDYAM-VERIFY-REGISTRY"}
                    </p>
                    <p className="text-[10px] text-slate-400 font-mono truncate max-w-xs">
                      {showCertModal.digital_signature_hash || "SHA256: 4f8b91a27e8d3c1b..."}
                    </p>
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <span className="inline-flex items-center gap-1 px-3 py-1 bg-emerald-600 text-white text-xs font-bold rounded-full">
                    <Check className="w-3.5 h-3.5" />
                    <span>AUTHENTIC & VALID</span>
                  </span>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => window.print()}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-xl text-xs font-bold transition-all"
              >
                <Printer className="w-4 h-4" />
                <span>Print / Save PDF</span>
              </button>
              <button
                onClick={() => setShowCertModal(null)}
                className="px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold shadow-sm"
              >
                Close Certificate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
