import { useState, useEffect } from "react";
import {
  Calendar,
  Users,
  CheckCircle2,
  Clock,
  ShieldCheck,
  Plus,
  X,
  FileCheck,
  Building,
  MapPin,
  Camera,
} from "lucide-react";
import {
  fetchInspections,
  scheduleCommonInspection,
  submitInspectionReport,
  fetchApplications,
  fetchDepartments,
} from "../api/client";

export default function InspectionsPage() {
  const [inspections, setInspections] = useState([]);
  const [applications, setApplications] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Modals
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [activeInsp, setActiveInsp] = useState(null);

  // Schedule form
  const [appId, setAppId] = useState("");
  const [scheduledDate, setScheduledDate] = useState("2026-03-20");
  const [timeSlot, setTimeSlot] = useState("Morning (10:00 - 13:00)");
  const [selectedDepts, setSelectedDepts] = useState(["DEPT-FIRE", "DEPT-PCB"]);
  const [notes, setNotes] = useState("");

  // Report form
  const [verdict, setVerdict] = useState("SATISFACTORY");
  const [reportText, setReportText] = useState("");
  const [findingsText, setFindingsText] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [inspData, appData, deptData] = await Promise.all([
        fetchInspections(),
        fetchApplications(),
        fetchDepartments(),
      ]);
      setInspections(inspData);
      setApplications(appData);
      setDepartments(deptData);
      if (appData.length > 0) setAppId(appData[0].application_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSchedule(e) {
    e.preventDefault();
    if (!appId || selectedDepts.length === 0) return;
    try {
      await scheduleCommonInspection({
        application_id: appId,
        scheduled_date: scheduledDate,
        time_slot: timeSlot,
        departments: selectedDepts,
        notes: notes || "Coordinated Joint Multi-Department Physical Site Verification",
      });
      setShowScheduleModal(false);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleReport(e) {
    e.preventDefault();
    if (!activeInsp) return;
    const findingsList = findingsText
      .split("\n")
      .map((f) => f.trim())
      .filter(Boolean);
    try {
      await submitInspectionReport(activeInsp.inspection_id, {
        verdict,
        report_text: reportText,
        findings: findingsList.length ? findingsList : ["All parameters verified satisfactorily on site."],
      });
      setShowReportModal(false);
      setReportText("");
      setFindingsText("");
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-800 tracking-tight">
            Common Multi-Department Inspection Planning
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Replaces independent, redundant departmental site visits with a unified joint inspection schedule.
          </p>
        </div>
        <button
          onClick={() => setShowScheduleModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Schedule Joint Inspection</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700 font-bold">Dismiss</button>
        </div>
      )}

      {/* Inspections Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {inspections.map((insp) => {
          const isCompleted = insp.status === "COMPLETED";

          return (
            <div
              key={insp.inspection_id}
              className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-4 hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-slate-700 bg-slate-100 px-2.5 py-0.5 rounded">
                    {insp.inspection_id}
                  </span>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                      isCompleted ? "bg-emerald-100 text-emerald-800" : "bg-sky-100 text-sky-800"
                    }`}
                  >
                    {insp.status}
                  </span>
                </div>

                <div>
                  <h3 className="font-bold text-slate-900 text-sm">{insp.enterprise_name}</h3>
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-1">
                    <Calendar className="w-3.5 h-3.5 text-sky-600" />
                    <span>{insp.scheduled_date}</span>
                    <span className="text-slate-300">•</span>
                    <span>{insp.time_slot}</span>
                  </div>
                </div>

                {/* Participating Departments */}
                <div className="space-y-1">
                  <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    Joint Inspecting Agencies:
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {insp.departments.map((d) => (
                      <span key={d} className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[11px] font-semibold">
                        {d.replace("DEPT-", "")}
                      </span>
                    ))}
                  </div>
                </div>

                {insp.notes && (
                  <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-xl border border-slate-200/60 leading-relaxed">
                    "{insp.notes}"
                  </p>
                )}

                {isCompleted && (
                  <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200/80 text-xs text-emerald-900 space-y-1.5">
                    <div className="flex items-center justify-between font-bold">
                      <span>Verdict:</span>
                      <span className="uppercase text-emerald-800">{insp.verdict}</span>
                    </div>
                    {insp.report_text && <p className="text-[11px] opacity-90">"{insp.report_text}"</p>}
                  </div>
                )}
              </div>

              {!isCompleted && (
                <div className="pt-3 border-t border-slate-100">
                  <button
                    onClick={() => {
                      setActiveInsp(insp);
                      setShowReportModal(true);
                    }}
                    className="w-full py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-xs transition-colors"
                  >
                    Submit Joint Inspection Report
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Schedule Modal */}
      {showScheduleModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-scaleIn">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-800 text-base">Schedule Common Inspection</h3>
              <button onClick={() => setShowScheduleModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSchedule} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Select Application
                </label>
                <select
                  value={appId}
                  onChange={(e) => setAppId(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-800"
                >
                  {applications.map((a) => (
                    <option key={a.application_id} value={a.application_id}>
                      {a.application_number} — {a.enterprise_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                    Date of Inspection
                  </label>
                  <input
                    type="date"
                    value={scheduledDate}
                    onChange={(e) => setScheduledDate(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2 text-xs text-slate-800"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                    Time Window
                  </label>
                  <select
                    value={timeSlot}
                    onChange={(e) => setTimeSlot(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2 text-xs text-slate-800"
                  >
                    <option value="Morning (10:00 - 13:00)">Morning (10:00 - 13:00)</option>
                    <option value="Afternoon (14:00 - 17:00)">Afternoon (14:00 - 17:00)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Select Participating Departments
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {departments.map((dept) => {
                    const isChecked = selectedDepts.includes(dept.department_id);
                    return (
                      <label key={dept.department_id} className="flex items-center gap-2 p-2 bg-slate-50 rounded-lg text-xs cursor-pointer">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            if (e.target.checked) setSelectedDepts([...selectedDepts, dept.department_id]);
                            else setSelectedDepts(selectedDepts.filter((d) => d !== dept.department_id));
                          }}
                          className="rounded text-sky-600"
                        />
                        <span className="font-semibold text-slate-700">{dept.name}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowScheduleModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 rounded-xl text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={selectedDepts.length === 0}
                  className="px-5 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold"
                >
                  Confirm Common Inspection
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Report Modal */}
      {showReportModal && activeInsp && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-scaleIn">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-800 text-base">Submit Joint Inspection Report</h3>
              <button onClick={() => setShowReportModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleReport} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Joint Inspection Verdict
                </label>
                <select
                  value={verdict}
                  onChange={(e) => setVerdict(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-800"
                >
                  <option value="SATISFACTORY">Satisfactory — Complies with all statutory parameters</option>
                  <option value="CONDITIONAL">Conditional — Minor observations to be rectified in 15 days</option>
                  <option value="UNSATISFACTORY">Unsatisfactory — Major statutory non-compliance observed</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Officer Detailed Observations & Summary
                </label>
                <textarea
                  value={reportText}
                  onChange={(e) => setReportText(e.target.value)}
                  placeholder="Record summary of joint on-site inspection, setback verification, ventilation, effluent handling..."
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-800"
                  rows={3}
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Key Findings (One per line)
                </label>
                <textarea
                  value={findingsText}
                  onChange={(e) => setFindingsText(e.target.value)}
                  placeholder="1. Front setback: 6 meters confirmed&#10;2. Underground reservoir: 100,000L confirmed"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-800"
                  rows={3}
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowReportModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 rounded-xl text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold"
                >
                  Sign & Submit Joint Report
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
