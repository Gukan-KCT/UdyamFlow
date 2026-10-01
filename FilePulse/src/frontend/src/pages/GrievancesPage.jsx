import { useState, useEffect } from "react";
import {
  Scale,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Plus,
  X,
  ArrowUpRight,
  ShieldAlert,
  Send,
  Building,
} from "lucide-react";
import {
  fetchGrievances,
  fileGrievance,
  escalateGrievance,
  resolveGrievance,
  fetchDepartments,
} from "../api/client";

export default function GrievancesPage() {
  const [grievances, setGrievances] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Modals
  const [showFileModal, setShowFileModal] = useState(false);
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [activeGrievance, setActiveGrievance] = useState(null);

  // File Form
  const [deptId, setDeptId] = useState("DEPT-LAB");
  const [category, setCategory] = useState("Delay in Scrutiny");
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");

  // Resolve Form
  const [resolveStatus, setResolveStatus] = useState("RESOLVED");
  const [resolutionNotes, setResolutionNotes] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [gData, dData] = await Promise.all([
        fetchGrievances(),
        fetchDepartments(),
      ]);
      setGrievances(gData);
      setDepartments(dData);
      if (dData.length > 0) setDeptId(dData[0].department_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleFile(e) {
    e.preventDefault();
    if (!subject || !description) return;
    try {
      await fileGrievance({
        department_id: deptId,
        category,
        subject,
        description,
      });
      setShowFileModal(false);
      setSubject("");
      setDescription("");
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleEscalate(grievanceId) {
    try {
      await escalateGrievance(grievanceId);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleResolve(e) {
    e.preventDefault();
    if (!activeGrievance) return;
    try {
      await resolveGrievance(activeGrievance.grievance_id, resolveStatus, resolutionNotes);
      setShowResolveModal(false);
      setResolutionNotes("");
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-800 tracking-tight">
            Multi-Tier Grievance Redressal & Escalation
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Statutory escalation mechanism with SLA tracking: Level 1 (Dept Nodal) → Level 2 (District Collector) → Level 3 (State Appellate).
          </p>
        </div>
        <button
          onClick={() => setShowFileModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Lodge Statutory Grievance</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700 font-bold">Dismiss</button>
        </div>
      )}

      {/* Grievances List */}
      <div className="space-y-4">
        {grievances.map((grv) => {
          const isResolved = grv.status === "RESOLVED" || grv.status === "CLOSED";
          const isEscalated = grv.status === "ESCALATED";

          return (
            <div
              key={grv.grievance_id}
              className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-4 hover:shadow-md transition-all"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="font-mono text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                      {grv.grievance_number}
                    </span>
                    <span className="px-2.5 py-0.5 bg-rose-50 text-rose-700 border border-rose-200 rounded-full text-xs font-bold">
                      Level {grv.level}: {grv.level === 1 ? "Department Nodal" : grv.level === 2 ? "District Collector" : "State Appellate"}
                    </span>
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                        isResolved
                          ? "bg-emerald-100 text-emerald-800"
                          : isEscalated
                          ? "bg-amber-100 text-amber-800 animate-pulse"
                          : "bg-rose-100 text-rose-800"
                      }`}
                    >
                      {grv.status}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-slate-900">{grv.subject}</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Against: <span className="font-medium text-slate-700">{grv.department_name}</span> • Category: <span className="font-medium text-slate-700">{grv.category}</span> • Filed: {new Date(grv.filed_at).toLocaleDateString()}
                  </p>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <div className="text-right text-xs">
                    <p className="text-[10px] text-slate-400 uppercase font-bold">Redressal SLA</p>
                    <p className="font-bold text-slate-800">{new Date(grv.deadline_at).toLocaleDateString()}</p>
                  </div>
                </div>
              </div>

              <p className="text-xs text-slate-700 bg-slate-50 p-3.5 rounded-xl border border-slate-200/60 leading-relaxed">
                "{grv.description}"
              </p>

              {grv.resolution_notes && (
                <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200/80 text-xs text-emerald-950">
                  <p className="font-bold">Official Resolution Findings:</p>
                  <p className="text-[11px] opacity-90 mt-0.5">"{grv.resolution_notes}"</p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-4">
                <span className="text-[11px] text-slate-400">
                  Statutory Escalation Window: 7 Business Days
                </span>

                <div className="flex items-center gap-2">
                  {!isResolved && (
                    <>
                      <button
                        onClick={() => handleEscalate(grv.grievance_id)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 rounded-lg text-xs font-bold transition-colors"
                      >
                        <ArrowUpRight className="w-3.5 h-3.5" />
                        <span>Escalate to Level {grv.level + 1}</span>
                      </button>

                      <button
                        onClick={() => {
                          setActiveGrievance(grv);
                          setShowResolveModal(true);
                        }}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition-colors shadow-xs"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Record Resolution</span>
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Lodge Grievance Modal */}
      {showFileModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-scaleIn">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-800 text-base">Lodge Statutory Grievance</h3>
              <button onClick={() => setShowFileModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleFile} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Respondent Department
                </label>
                <select
                  value={deptId}
                  onChange={(e) => setDeptId(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-800"
                >
                  {departments.map((d) => (
                    <option key={d.department_id} value={d.department_id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Grievance Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-800"
                >
                  <option value="Delay in Scrutiny">Delay in Scrutiny beyond Statutory SLA</option>
                  <option value="Unreasonable Query">Unreasonable / Repetitive Clarification Query</option>
                  <option value="Inspection Delay">Delay in Scheduling or Uploading Inspection Report</option>
                  <option value="Technical Issue">Portal Payment / Document Upload Issue</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Subject Summary
                </label>
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="e.g. Scrutiny delayed beyond 15 days for Factory Plan approval"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-800"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Detailed Grievance Narrative
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Specify submission dates, application numbers, queries raised, and relief sought..."
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-800"
                  rows={4}
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowFileModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 rounded-xl text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold"
                >
                  File Grievance at Level 1
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Resolve Modal */}
      {showResolveModal && activeGrievance && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-scaleIn">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-800 text-base">Record Grievance Resolution</h3>
              <button onClick={() => setShowResolveModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleResolve} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Resolution Decision
                </label>
                <select
                  value={resolveStatus}
                  onChange={(e) => setResolveStatus(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-800"
                >
                  <option value="RESOLVED">Resolved — Relief Granted to Applicant</option>
                  <option value="CLOSED">Closed — Disposed with Statutory Clarification</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Official Resolution Findings & Notes
                </label>
                <textarea
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  placeholder="Record corrective actions taken, file unblocked, and clearance issued..."
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-800"
                  rows={4}
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowResolveModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 rounded-xl text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold"
                >
                  Submit Official Resolution
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
