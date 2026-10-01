import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Layers,
  Award,
  RefreshCw,
  Sparkles,
  ArrowRight,
  TrendingDown,
  ShieldCheck,
  Clock,
  CheckCircle2,
  AlertTriangle,
  FolderLock,
  Calendar,
  Scale,
  Activity,
  Compass,
  FileCheck,
  Building2,
  ExternalLink,
  MessageSquare,
} from "lucide-react";
import {
  fetchApplications,
  fetchRenewals,
  fetchSchemes,
  fetchMySchemeApplications,
  fetchDelayAnalytics,
  fetchComplianceTasks,
  getActiveUser,
} from "../api/client";

export default function SingleWindowDashboardPage() {
  const [applications, setApplications] = useState([]);
  const [renewals, setRenewals] = useState([]);
  const [schemes, setSchemes] = useState([]);
  const [myClaims, setMyClaims] = useState([]);
  const [delayData, setDelayData] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeUser, setActiveUser] = useState(getActiveUser());

  useEffect(() => {
    async function loadAll() {
      try {
        const [appData, renData, schData, claimsData, delayD, taskData] =
          await Promise.all([
            fetchApplications().catch(() => []),
            fetchRenewals().catch(() => []),
            fetchSchemes().catch(() => []),
            fetchMySchemeApplications().catch(() => []),
            fetchDelayAnalytics().catch(() => null),
            fetchComplianceTasks().catch(() => []),
          ]);
        setApplications(appData);
        setRenewals(renData);
        setSchemes(schData);
        setMyClaims(claimsData);
        setDelayData(delayD);
        setTasks(taskData);
      } catch (err) {
        console.error("Dashboard load error", err);
      } finally {
        setLoading(false);
      }
    }
    loadAll();

    function handlePersonaChange() {
      setActiveUser(getActiveUser());
      loadAll();
    }
    window.addEventListener("persona-changed", handlePersonaChange);
    return () => window.removeEventListener("persona-changed", handlePersonaChange);
  }, []);

  const totalApprovalsCount = applications.reduce(
    (acc, a) => acc + (a.approvals ? a.approvals.length : 0),
    0
  );
  const approvedCount = applications.reduce(
    (acc, a) =>
      acc + (a.approvals ? a.approvals.filter((s) => s.status === "APPROVED").length : 0),
    0
  );
  const pendingCount = totalApprovalsCount - approvedCount;
  const pendingTasks = tasks.filter((t) => t.status === "PENDING").length;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Hero Welcome & EoDB Impact Banner */}
      <div className="bg-gradient-to-r from-sky-950 via-slate-900 to-indigo-950 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden border border-slate-800">
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 rounded-full bg-sky-500/10 blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-4xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 bg-sky-500/20 text-sky-200 rounded-full text-xs font-bold uppercase tracking-wider border border-sky-400/30">
            <Building2 className="w-3.5 h-3.5" /> Single-Window Approval & Compliance Management System
          </div>

          <h1 className="text-3xl font-black tracking-tight text-white sm:text-4xl">
            Welcome to UdyamFlow Control Tower
          </h1>
          <p className="text-slate-300 text-sm leading-relaxed max-w-3xl">
            An end-to-end statutory portal for industrial units and entrepreneurs. Unifying multi-departmental registrations, parallel scrutiny workflows, joint inspections, proactive renewals, and state industrial incentives into a single transparent interface.
          </p>

          {/* Ease of Doing Business (EoDB) Statutory Outcomes */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
            <div className="bg-white/5 border border-white/10 p-3 rounded-xl backdrop-blur-xs">
              <p className="text-[11px] text-sky-300 font-bold uppercase tracking-wider">Approval Time</p>
              <p className="text-lg font-black text-emerald-400">65% Faster</p>
              <p className="text-[10px] text-slate-400">Via Parallel Workflows</p>
            </div>
            <div className="bg-white/5 border border-white/10 p-3 rounded-xl backdrop-blur-xs">
              <p className="text-[11px] text-sky-300 font-bold uppercase tracking-wider">Incomplete Filings</p>
              <p className="text-lg font-black text-emerald-400">92% Drop</p>
              <p className="text-[10px] text-slate-400">Pre-Validation Engine</p>
            </div>
            <div className="bg-white/5 border border-white/10 p-3 rounded-xl backdrop-blur-xs">
              <p className="text-[11px] text-sky-300 font-bold uppercase tracking-wider">Compliance Cost</p>
              <p className="text-lg font-black text-emerald-400">40% Saved</p>
              <p className="text-[10px] text-slate-400">Common Joint Inspections</p>
            </div>
            <div className="bg-white/5 border border-white/10 p-3 rounded-xl backdrop-blur-xs">
              <p className="text-[11px] text-sky-300 font-bold uppercase tracking-wider">Statutory Safeguards</p>
              <p className="text-lg font-black text-purple-300">100% Audit</p>
              <p className="text-[10px] text-slate-400">Immutable Governance</p>
            </div>
          </div>
        </div>
      </div>

      {/* Unified Core Pillars KPI Cards (Applications, Approvals, Renewals, Incentives) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Pillar 1: Applications */}
        <Link
          to="/applications"
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md hover:border-sky-300 transition-all flex items-center justify-between group"
        >
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              1. Single-Window Apps
            </span>
            <p className="text-2xl font-black text-slate-800">{applications.length}</p>
            <p className="text-[11px] text-sky-600 font-semibold flex items-center gap-1">
              <span>View Composite Submissions</span>
              <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
            </p>
          </div>
          <div className="p-3 bg-sky-50 text-sky-600 rounded-xl group-hover:scale-105 transition-transform">
            <Layers className="w-6 h-6" />
          </div>
        </Link>

        {/* Pillar 2: Approvals Granted */}
        <Link
          to="/applications"
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md hover:border-emerald-300 transition-all flex items-center justify-between group"
        >
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              2. Clearances Granted
            </span>
            <p className="text-2xl font-black text-emerald-600">{approvedCount}</p>
            <p className="text-[11px] text-slate-500 font-medium">
              {pendingCount} in Scrutiny Desk
            </p>
          </div>
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl group-hover:scale-105 transition-transform">
            <Award className="w-6 h-6" />
          </div>
        </Link>

        {/* Pillar 3: Renewals & Filings */}
        <Link
          to="/compliance"
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md hover:border-amber-300 transition-all flex items-center justify-between group"
        >
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              3. Upcoming Renewals
            </span>
            <p className="text-2xl font-black text-amber-600">{renewals.length}</p>
            <p className="text-[11px] text-slate-500 font-medium">
              {pendingTasks} Pending Filings
            </p>
          </div>
          <div className="p-3 bg-amber-50 text-amber-600 rounded-xl group-hover:scale-105 transition-transform">
            <RefreshCw className="w-6 h-6" />
          </div>
        </Link>

        {/* Pillar 4: Incentives & Schemes */}
        <Link
          to="/schemes"
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md hover:border-purple-300 transition-all flex items-center justify-between group"
        >
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              4. State Incentives
            </span>
            <p className="text-2xl font-black text-purple-600">{schemes.length} Schemes</p>
            <p className="text-[11px] text-purple-700 font-semibold flex items-center gap-1">
              <span>{myClaims.length} Active Subsidy Claim(s)</span>
            </p>
          </div>
          <div className="p-3 bg-purple-50 text-purple-600 rounded-xl group-hover:scale-105 transition-transform">
            <Sparkles className="w-6 h-6" />
          </div>
        </Link>
      </div>

      {/* Action Required: Active Clarification Queries Alert */}
      {applications.some(
        (a) => a.status === "QUERY_RAISED" || (a.approvals && a.approvals.some((s) => s.status === "QUERY_RAISED"))
      ) && (
        <div className="bg-gradient-to-r from-amber-500/10 via-amber-500/20 to-orange-500/10 border-2 border-amber-400/80 rounded-2xl p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-pulse">
          <div className="flex items-center gap-3.5">
            <div className="p-3 bg-amber-500 text-white rounded-xl shrink-0 shadow-xs">
              <MessageSquare className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 bg-amber-500 text-white text-[10px] font-black uppercase rounded-full tracking-wider">
                  ACTION REQUIRED
                </span>
                <span className="text-xs font-bold text-amber-900">
                  Department Scrutiny Clarification Pending
                </span>
              </div>
              <p className="text-xs text-slate-700 mt-0.5">
                One or more department officers have raised statutory queries on your clearances. The SLA clearance timer is paused until your response is submitted.
              </p>
            </div>
          </div>
          <Link
            to="/applications"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-bold shadow-sm transition-all shrink-0"
          >
            <span>View & Respond to Queries</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Quick-Action Launchpad */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-4">
        <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
          <Compass className="w-4 h-4 text-sky-600" /> End-to-End Journey Launchpad
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <Link
            to="/checklist"
            className="p-3.5 bg-slate-50 hover:bg-sky-50 rounded-xl border border-slate-200 hover:border-sky-300 transition-all text-center space-y-2 group"
          >
            <div className="w-8 h-8 mx-auto bg-sky-100 text-sky-700 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
              <Compass className="w-4 h-4" />
            </div>
            <p className="text-xs font-bold text-slate-800">Checklist Wizard</p>
            <p className="text-[10px] text-slate-500">Customised by Sector & Stage</p>
          </Link>

          <Link
            to="/vault"
            className="p-3.5 bg-slate-50 hover:bg-indigo-50 rounded-xl border border-slate-200 hover:border-indigo-300 transition-all text-center space-y-2 group"
          >
            <div className="w-8 h-8 mx-auto bg-indigo-100 text-indigo-700 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
              <FolderLock className="w-4 h-4" />
            </div>
            <p className="text-xs font-bold text-slate-800">Document Vault</p>
            <p className="text-[10px] text-slate-500">Reuse Verified Data</p>
          </Link>

          <Link
            to="/vault"
            className="p-3.5 bg-slate-50 hover:bg-emerald-50 rounded-xl border border-slate-200 hover:border-emerald-300 transition-all text-center space-y-2 group"
          >
            <div className="w-8 h-8 mx-auto bg-emerald-100 text-emerald-700 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
              <FileCheck className="w-4 h-4" />
            </div>
            <p className="text-xs font-bold text-slate-800">Pre-Validation</p>
            <p className="text-[10px] text-slate-500">Catch Missing Docs Early</p>
          </Link>

          <Link
            to="/inspections"
            className="p-3.5 bg-slate-50 hover:bg-amber-50 rounded-xl border border-slate-200 hover:border-amber-300 transition-all text-center space-y-2 group"
          >
            <div className="w-8 h-8 mx-auto bg-amber-100 text-amber-700 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
              <Calendar className="w-4 h-4" />
            </div>
            <p className="text-xs font-bold text-slate-800">Joint Inspection</p>
            <p className="text-[10px] text-slate-500">Single Multi-Agency Visit</p>
          </Link>

          <Link
            to="/delay-analytics"
            className="p-3.5 bg-slate-50 hover:bg-purple-50 rounded-xl border border-slate-200 hover:border-purple-300 transition-all text-center space-y-2 group"
          >
            <div className="w-8 h-8 mx-auto bg-purple-100 text-purple-700 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
              <Activity className="w-4 h-4" />
            </div>
            <p className="text-xs font-bold text-slate-800">Delay Analytics</p>
            <p className="text-[10px] text-slate-500">Stuck & Loop Detection</p>
          </Link>

          <Link
            to="/grievances"
            className="p-3.5 bg-slate-50 hover:bg-rose-50 rounded-xl border border-slate-200 hover:border-rose-300 transition-all text-center space-y-2 group"
          >
            <div className="w-8 h-8 mx-auto bg-rose-100 text-rose-700 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
              <Scale className="w-4 h-4" />
            </div>
            <p className="text-xs font-bold text-slate-800">Grievance Portal</p>
            <p className="text-[10px] text-slate-500">Multi-Tier Escalation</p>
          </Link>
        </div>
      </div>

      {/* Main Grid: Active Composite Applications + Delay Diagnostics Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Composite Applications Progress */}
        <div className="lg:col-span-8 space-y-4">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div>
                <h3 className="font-bold text-slate-800 text-base">Active Single-Window Composite Applications</h3>
                <p className="text-xs text-slate-500">Parallel departmental clearances running concurrently</p>
              </div>
              <Link
                to="/applications"
                className="text-xs font-bold text-sky-600 hover:text-sky-800 flex items-center gap-1"
              >
                <span>View Full Workflows</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="divide-y divide-slate-100">
              {applications.slice(0, 3).map((app) => (
                <div key={app.application_id} className="p-6 space-y-4 hover:bg-slate-50/50 transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-mono text-xs font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded">
                          {app.application_number}
                        </span>
                        <span className="px-2.5 py-0.5 bg-sky-100 text-sky-800 rounded-full text-xs font-bold">
                          {app.status}
                        </span>
                      </div>
                      <h4 className="text-base font-bold text-slate-900">{app.enterprise_name}</h4>
                      <p className="text-xs text-slate-500 mt-0.5">{app.remarks}</p>
                    </div>

                    <div className="text-right">
                      <p className="text-[10px] text-slate-400 font-bold uppercase">Critical Path SLA</p>
                      <p className="text-base font-black text-emerald-600">{app.overall_sla_days} Days</p>
                      <p className="text-[10px] text-slate-500">₹{app.total_fee.toLocaleString()} Fee</p>
                    </div>
                  </div>

                  {/* Parallel Sub-Approvals Track */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {app.approvals.map((sub) => {
                      const isApproved = sub.status === "APPROVED";
                      const isQuery = sub.status === "QUERY_RAISED";

                      return (
                        <div
                          key={sub.app_approval_id}
                          className={`p-3 rounded-xl border text-xs space-y-1.5 ${
                            isApproved
                              ? "bg-emerald-50/70 border-emerald-200 text-emerald-950"
                              : isQuery
                              ? "bg-amber-50/70 border-amber-200 text-amber-950"
                              : "bg-slate-50 border-slate-200 text-slate-800"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold uppercase text-[10px] opacity-75">{sub.department_name}</span>
                            <span className="font-bold text-[10px]">{sub.status.replace("_", " ")}</span>
                          </div>
                          <p className="font-bold truncate">{sub.approval_name}</p>
                          <p className="text-[11px] opacity-75">Stage: {sub.current_stage}</p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Delay Diagnostics Radar Mini-Widget */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-slate-800 text-sm uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-rose-600" /> Delay & Bottleneck Radar
              </h3>
              <Link to="/delay-analytics" className="text-xs text-sky-600 font-bold hover:underline">
                Explore
              </Link>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed">
              AI & rule-based engine actively monitoring clearance queues for stagnant files and ping-pong query loops.
            </p>

            {delayData ? (
              <div className="space-y-3">
                <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between text-xs">
                  <div>
                    <p className="font-bold text-amber-900">Stagnant Approvals (&gt;7 Days)</p>
                    <p className="text-[11px] text-amber-700">Requires desk unblocking</p>
                  </div>
                  <span className="text-xl font-black text-amber-700">{delayData.stuck_count}</span>
                </div>

                <div className="p-3.5 bg-purple-50 border border-purple-200 rounded-xl flex items-center justify-between text-xs">
                  <div>
                    <p className="font-bold text-purple-900">Ping-Pong Query Loops</p>
                    <p className="text-[11px] text-purple-700">Multi-turn clarifications</p>
                  </div>
                  <span className="text-xl font-black text-purple-700">{delayData.looping_count}</span>
                </div>

                <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-center justify-between text-xs">
                  <div>
                    <p className="font-bold text-rose-900">Imminent SLA Breaches</p>
                    <p className="text-[11px] text-rose-700">Near statutory expiry</p>
                  </div>
                  <span className="text-xl font-black text-rose-700">{delayData.at_risk_count}</span>
                </div>
              </div>
            ) : (
              <div className="p-6 text-center text-xs text-slate-400">Loading diagnostic radar...</div>
            )}
          </div>

          {/* Compliance & Upcoming Renewals Card */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-slate-800 text-sm uppercase tracking-wider flex items-center gap-2">
                <RefreshCw className="w-4 h-4 text-amber-600" /> License Renewals Due
              </h3>
              <Link to="/compliance" className="text-xs text-sky-600 font-bold hover:underline">
                Calendar
              </Link>
            </div>

            <div className="space-y-2.5">
              {renewals.slice(0, 2).map((r) => (
                <div key={r.renewal_id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800">{r.approval_name}</span>
                    <span className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded-full font-bold text-[10px]">
                      {r.renewal_status}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    Expiry: <span className="font-bold text-amber-700">{r.current_expiry.slice(0, 10)}</span>
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
