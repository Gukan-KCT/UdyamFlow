import { useState, useEffect } from "react";
import {
  Calendar,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Award,
  QrCode,
  ShieldCheck,
  RefreshCw,
  Search,
  ExternalLink,
} from "lucide-react";
import {
  fetchComplianceTasks,
  completeComplianceTask,
  fetchRenewals,
  verifyCertificatePublic,
} from "../api/client";

export default function ComplianceRenewalsPage() {
  const [tasks, setTasks] = useState([]);
  const [renewals, setRenewals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Verification Portal State
  const [verifyCode, setVerifyCode] = useState("CERT-2026-PCBAUTO1");
  const [verificationResult, setVerificationResult] = useState(null);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [tData, rData] = await Promise.all([
        fetchComplianceTasks(),
        fetchRenewals(),
      ]);
      setTasks(tData);
      setRenewals(rData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCompleteTask(taskId) {
    try {
      await completeComplianceTask(taskId);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleVerify(e) {
    e.preventDefault();
    if (!verifyCode.trim()) return;
    setVerifying(true);
    try {
      const res = await verifyCertificatePublic(verifyCode.trim());
      setVerificationResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setVerifying(false);
    }
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-emerald-950 via-teal-950 to-slate-900 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/20 text-emerald-200 rounded-full text-xs font-semibold uppercase tracking-wider mb-4 border border-emerald-400/30">
            <ShieldCheck className="w-3.5 h-3.5" /> Post-Establishment Compliance Engine
          </div>
          <h1 className="text-3xl font-black tracking-tight text-white mb-2">
            Compliance Calendar & Renewal Alerts
          </h1>
          <p className="text-emerald-100/90 text-sm leading-relaxed">
            Stay statutory-compliant with proactive alerts for recurring filings, periodic safety returns, and 30/60/90-day license renewal countdowns.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700 font-bold">Dismiss</button>
        </div>
      )}

      {/* Grid: Compliance Tasks + Renewals */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Statutory Compliance Calendar */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div>
                <h3 className="font-bold text-slate-800 text-base">Annual & Periodic Statutory Filings</h3>
                <p className="text-xs text-slate-500">Track pollution returns, labour reports, and safety audits</p>
              </div>
              <span className="text-xs font-bold text-sky-600 bg-sky-50 px-2.5 py-1 rounded-full">
                {tasks.filter((t) => t.status === "PENDING").length} Pending Filings
              </span>
            </div>

            <div className="divide-y divide-slate-100">
              {tasks.map((task) => {
                const isCompleted = task.status === "COMPLETED";

                return (
                  <div key={task.task_id} className="p-5 hover:bg-slate-50/60 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold px-2 py-0.5 bg-slate-100 text-slate-700 rounded uppercase">
                          {task.category}
                        </span>
                        <span className="text-[10px] text-slate-400 font-medium">
                          Period: {task.recurring_period}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            isCompleted ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {task.status}
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-slate-900">{task.title}</h4>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Agency: <span className="font-medium text-slate-700">{task.department_name}</span> • Act: <span className="font-mono text-[11px] text-slate-600">{task.statutory_ref}</span>
                      </p>
                      <div className="flex items-center gap-1 text-xs font-semibold text-slate-600 mt-2">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>Due Date: {task.due_date}</span>
                      </div>
                    </div>

                    {!isCompleted && (
                      <button
                        onClick={() => handleCompleteTask(task.task_id)}
                        className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-xs transition-colors shrink-0"
                      >
                        Mark Completed
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Renewals & Public QR Verification */}
        <div className="lg:col-span-5 space-y-6">
          {/* Upcoming Renewals */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-4">
            <h3 className="font-bold text-slate-800 text-base flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-sky-600" /> Upcoming Approval Renewals
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Automated single-window renewal pipeline triggers 30-60 days before validity expiration.
            </p>

            <div className="space-y-3">
              {renewals.map((r) => (
                <div key={r.renewal_id} className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-slate-700">{r.certificate_number}</span>
                    <span className="px-2 py-0.5 bg-sky-100 text-sky-800 rounded-full text-[10px] font-bold">
                      {r.renewal_status}
                    </span>
                  </div>
                  <p className="text-xs font-bold text-slate-800">{r.approval_name}</p>
                  <p className="text-[11px] text-slate-500">
                    Expiry: <span className="font-bold text-amber-700">{r.current_expiry.slice(0, 10)}</span>
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Public Certificate QR Verification Portal */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-4">
            <h3 className="font-bold text-slate-800 text-base flex items-center gap-2">
              <QrCode className="w-4 h-4 text-emerald-600" /> Public Certificate Verification
            </h3>
            <p className="text-xs text-slate-500">
              Verify statutory digital certificates issued across all state departments using QR code or certificate ID:
            </p>

            <form onSubmit={handleVerify} className="space-y-3">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={verifyCode}
                  onChange={(e) => setVerifyCode(e.target.value)}
                  placeholder="Enter Certificate No or QR Code"
                  className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  required
                />
                <button
                  type="submit"
                  disabled={verifying}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-xs shrink-0"
                >
                  Verify
                </button>
              </div>
            </form>

            {verificationResult && (
              <div
                className={`p-4 rounded-xl border text-xs space-y-2 ${
                  verificationResult.valid
                    ? "bg-emerald-50/70 border-emerald-200 text-emerald-950"
                    : "bg-rose-50/70 border-rose-200 text-rose-950"
                }`}
              >
                <div className="flex items-center gap-2 font-bold">
                  {verificationResult.valid ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                  )}
                  <span>{verificationResult.valid ? "GENUINE STATUTORY CLEARANCE" : "UNVERIFIED / INVALID"}</span>
                </div>

                {verificationResult.valid && (
                  <div className="space-y-1 text-[11px] opacity-90 font-medium">
                    <p>Clearance: <span className="font-bold">{verificationResult.approval_name}</span></p>
                    <p>Authority: <span className="font-bold">{verificationResult.department_name}</span></p>
                    <p>Unit: <span className="font-bold">{verificationResult.enterprise_name}</span></p>
                    <p>Digital Hash: <span className="font-mono">{verificationResult.digital_signature_hash?.slice(0, 16)}...</span></p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
