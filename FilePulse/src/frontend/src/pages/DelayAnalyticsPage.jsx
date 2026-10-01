import { useState, useEffect } from "react";
import {
  Activity,
  AlertTriangle,
  RotateCcw,
  Clock,
  Building2,
  TrendingUp,
  ShieldAlert,
  Zap,
  CheckCircle2,
  ChevronRight,
  Flame,
} from "lucide-react";
import {
  fetchDelayAnalytics,
  fetchDepartmentBottlenecks,
} from "../api/client";

export default function DelayAnalyticsPage() {
  const [delayData, setDelayData] = useState(null);
  const [bottlenecks, setBottlenecks] = useState([]);
  const [activeTab, setActiveTab] = useState("at_risk"); // at_risk | stuck | looping | bottlenecks
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [dData, bData] = await Promise.all([
        fetchDelayAnalytics(),
        fetchDepartmentBottlenecks(),
      ]);
      setDelayData(dData);
      setBottlenecks(bData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-sky-950 to-slate-900 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-sky-500/20 text-sky-200 rounded-full text-xs font-semibold uppercase tracking-wider mb-4 border border-sky-400/30">
            <Activity className="w-3.5 h-3.5" /> Delay Analytics Engine
          </div>
          <h1 className="text-3xl font-black tracking-tight text-white mb-2">
            Bottleneck Radar & SLA Analytics
          </h1>
          <p className="text-sky-100/90 text-sm leading-relaxed">
            Continuous diagnostic scanning across all departmental approvals. Pinpoint stagnant files, detect repetitive query loops, and unblock high-risk applications before statutory SLA expiration.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700 font-bold">Dismiss</button>
        </div>
      )}

      {/* Metric Cards */}
      {delayData && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-sky-50 text-sky-600 rounded-xl">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-slate-400">Active Clearances</p>
              <p className="text-2xl font-black text-slate-800">{delayData.total_active_approvals}</p>
              <p className="text-[11px] text-slate-500">Under Scrutiny</p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-amber-50 text-amber-600 rounded-xl">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-slate-400">Stuck &gt; 7 Days</p>
              <p className="text-2xl font-black text-amber-600">{delayData.stuck_count}</p>
              <p className="text-[11px] text-slate-500">Inactive Scrutiny Desks</p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-purple-50 text-purple-600 rounded-xl">
              <RotateCcw className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-slate-400">Query Loops</p>
              <p className="text-2xl font-black text-purple-600">{delayData.looping_count}</p>
              <p className="text-[11px] text-slate-500">Ping-Pong Cycles</p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-rose-50 text-rose-600 rounded-xl">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-slate-400">SLA Breach Risk</p>
              <p className="text-2xl font-black text-rose-600">{delayData.at_risk_count}</p>
              <p className="text-[11px] text-slate-500">Imminent SLA Expiry</p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="flex border-b border-slate-200/80 px-6 pt-3 bg-slate-50/50 gap-6">
          <button
            onClick={() => setActiveTab("at_risk")}
            className={`pb-3 text-xs font-bold transition-all relative ${
              activeTab === "at_risk"
                ? "text-rose-600"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            Imminent SLA Breach & At-Risk Clearances ({delayData?.at_risk_count || 0})
            {activeTab === "at_risk" && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-rose-600 rounded-full" />
            )}
          </button>

          <button
            onClick={() => setActiveTab("stuck")}
            className={`pb-3 text-xs font-bold transition-all relative ${
              activeTab === "stuck"
                ? "text-amber-600"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            Stuck & Rotting Clearances ({delayData?.stuck_count || 0})
            {activeTab === "stuck" && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-600 rounded-full" />
            )}
          </button>

          <button
            onClick={() => setActiveTab("looping")}
            className={`pb-3 text-xs font-bold transition-all relative ${
              activeTab === "looping"
                ? "text-purple-600"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            Ping-Pong Query Loops ({delayData?.looping_count || 0})
            {activeTab === "looping" && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-600 rounded-full" />
            )}
          </button>

          <button
            onClick={() => setActiveTab("bottlenecks")}
            className={`pb-3 text-xs font-bold transition-all relative ${
              activeTab === "bottlenecks"
                ? "text-sky-600"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            Departmental Benchmarks ({bottlenecks.length})
            {activeTab === "bottlenecks" && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-600 rounded-full" />
            )}
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === "bottlenecks" ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-400 uppercase tracking-wider font-bold">
                    <th className="pb-3">Department Agency</th>
                    <th className="pb-3 text-center">Workload</th>
                    <th className="pb-3 text-center">Query Rate %</th>
                    <th className="pb-3 text-center">Approval Rate %</th>
                    <th className="pb-3 text-center">Avg Risk Index</th>
                    <th className="pb-3 text-right">Avg SLA (Days)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {bottlenecks.map((b) => (
                    <tr key={b.department_id} className="hover:bg-slate-50">
                      <td className="py-3.5">
                        <p className="font-bold text-slate-900">{b.department_name}</p>
                        <p className="font-mono text-[10px] text-slate-400">{b.department_code}</p>
                      </td>
                      <td className="py-3.5 text-center font-bold text-slate-800">{b.total_workload}</td>
                      <td className="py-3.5 text-center">
                        <span className={`px-2 py-0.5 rounded-full font-bold ${b.query_rate_pct > 30 ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-700"}`}>
                          {b.query_rate_pct}%
                        </span>
                      </td>
                      <td className="py-3.5 text-center">
                        <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full font-bold">
                          {b.approval_rate_pct}%
                        </span>
                      </td>
                      <td className="py-3.5 text-center font-bold text-slate-700">{b.avg_risk_score}</td>
                      <td className="py-3.5 text-right font-bold text-slate-900">{b.avg_sla_days} Days</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="space-y-4">
              {(() => {
                const list =
                  activeTab === "at_risk"
                    ? delayData?.at_risk_approvals || []
                    : activeTab === "stuck"
                    ? delayData?.stuck_approvals || []
                    : delayData?.looping_approvals || [];

                if (list.length === 0) {
                  return (
                    <div className="p-8 text-center text-slate-400 text-xs">
                      No files currently detected under this alert criteria.
                    </div>
                  );
                }

                return list.map((item) => (
                  <div
                    key={item.app_approval_id}
                    className="p-5 rounded-xl border border-slate-200/80 bg-slate-50/40 hover:bg-slate-50 transition-all space-y-3"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono text-xs font-bold text-slate-800">
                            {item.application_number}
                          </span>
                          <span className="px-2 py-0.5 bg-sky-100 text-sky-700 rounded text-[10px] font-bold">
                            {item.department_name}
                          </span>
                          <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-semibold">
                            Stage: {item.current_stage}
                          </span>
                        </div>
                        <h4 className="text-sm font-bold text-slate-900">{item.approval_name}</h4>
                        <p className="text-xs text-slate-500 mt-0.5">{item.enterprise_name}</p>
                      </div>

                      <div className="flex items-center gap-3 shrink-0">
                        <div className="text-right">
                          <p className="text-[10px] text-slate-400 uppercase font-bold">Risk Index</p>
                          <p className="text-lg font-black text-rose-600">{item.risk_score} / 100</p>
                        </div>
                      </div>
                    </div>

                    <div className="p-3 bg-amber-500/10 border border-amber-300/40 rounded-xl text-xs text-amber-900 flex items-start gap-2.5">
                      <Zap className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <p className="leading-relaxed">
                        <span className="font-bold">Recommended Unblocker:</span> {item.ai_insight}
                      </p>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-200/60">
                      <span>Days Inactive: <strong className="text-slate-700">{item.days_inactive}</strong></span>
                      <span>Query Count: <strong className="text-slate-700">{item.query_count}</strong></span>
                      <span>Days to Deadline: <strong className={item.is_overdue ? "text-rose-600" : "text-slate-700"}>{item.days_to_deadline ?? "N/A"}</strong></span>
                    </div>
                  </div>
                ));
              })()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
