import { useState, useEffect } from "react";
import {
  Gift,
  Building2,
  DollarSign,
  CheckCircle2,
  Clock,
  Sparkles,
  ArrowRight,
  X,
  FileText,
  AlertCircle,
} from "lucide-react";
import {
  fetchSchemes,
  applyForScheme,
  fetchMySchemeApplications,
} from "../api/client";

export default function SchemesPage() {
  const [schemes, setSchemes] = useState([]);
  const [myApplications, setMyApplications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Apply Modal
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [selectedScheme, setSelectedScheme] = useState(null);
  const [claimAmount, setClaimAmount] = useState(2500000);
  const [remarks, setRemarks] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [sData, myApps] = await Promise.all([
        fetchSchemes(),
        fetchMySchemeApplications(),
      ]);
      setSchemes(sData);
      setMyApplications(myApps);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleApply(e) {
    e.preventDefault();
    if (!selectedScheme) return;
    try {
      await applyForScheme({
        scheme_id: selectedScheme.scheme_id,
        profile_id: "prof_apex_01",
        claim_amount: parseFloat(claimAmount),
        remarks,
      });
      setShowApplyModal(false);
      setRemarks("");
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-purple-950 via-indigo-950 to-slate-900 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-500/20 text-purple-200 rounded-full text-xs font-semibold uppercase tracking-wider mb-4 border border-purple-400/30">
            <Sparkles className="w-3.5 h-3.5" /> Industrial Policy Incentives & Subsidies
          </div>
          <h1 className="text-3xl font-black tracking-tight text-white mb-2">
            Government Schemes & Subsidies
          </h1>
          <p className="text-purple-100/90 text-sm leading-relaxed">
            Discover tailored capital subsidies, interest subvention, and power concessions available for MSME manufacturing units. 1-click claim filing backed by your verified business profile.
          </p>
          <div className="mt-4 flex items-center gap-3 text-xs bg-amber-500/10 border border-amber-400/30 text-amber-200 px-3.5 py-2 rounded-lg">
            <AlertCircle className="w-4 h-4 text-amber-300 shrink-0" />
            <span>SAMPLE / ILLUSTRATIVE INCENTIVES — Verify against official state policy guidelines for SIH evaluation.</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700 font-bold">Dismiss</button>
        </div>
      )}

      {/* Submitted Claims Bar */}
      {myApplications.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-4">
          <h3 className="font-bold text-slate-800 text-sm uppercase tracking-wider flex items-center gap-2">
            <FileText className="w-4 h-4 text-sky-600" /> My Submitted Incentive Claims ({myApplications.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {myApplications.map((app) => (
              <div key={app.scheme_app_id} className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-slate-700">{app.scheme_app_id}</span>
                  <span className="px-2.5 py-0.5 bg-sky-100 text-sky-800 rounded-full text-[10px] font-bold">
                    {app.status}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-900">{app.scheme_name}</h4>
                <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-200/60">
                  <span className="text-slate-500">Claim Amount: <span className="font-bold text-slate-800">₹{app.claim_amount.toLocaleString()}</span></span>
                  <span className="text-slate-400 text-[11px]">{new Date(app.submitted_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Available Schemes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {schemes.map((scheme) => (
          <div
            key={scheme.scheme_id}
            className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-all flex flex-col justify-between space-y-5"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 bg-purple-50 text-purple-700 border border-purple-200 text-xs font-bold rounded-full">
                  {scheme.incentive_type}
                </span>
                <span className="text-xs font-black text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full">
                  Max: ₹{(scheme.max_subsidy_inr / 100000).toFixed(0)} Lakhs
                </span>
              </div>

              <div>
                <h3 className="text-base font-bold text-slate-900">{scheme.name}</h3>
                <p className="text-xs text-slate-500 mt-0.5">{scheme.department_name}</p>
              </div>

              <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-200/60 leading-relaxed">
                {scheme.benefit_details}
              </p>

              <div>
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                  Eligibility Criteria:
                </p>
                <p className="text-xs text-slate-600">{scheme.eligibility_criteria}</p>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-4">
              <span className="text-[11px] text-slate-400 font-medium">
                Deadline: {scheme.application_deadline || "Open Ongoing"}
              </span>
              <button
                onClick={() => {
                  setSelectedScheme(scheme);
                  setShowApplyModal(true);
                }}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold shadow-xs transition-colors"
              >
                <span>Apply for Incentive</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Apply Modal */}
      {showApplyModal && selectedScheme && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-scaleIn">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-800 text-base">Incentive Subsidy Claim Form</h3>
              <button onClick={() => setShowApplyModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleApply} className="space-y-4">
              <div>
                <p className="text-xs text-slate-500 mb-1">Applying for:</p>
                <p className="text-sm font-bold text-slate-900">{selectedScheme.name}</p>
                <p className="text-xs text-purple-700 font-semibold">{selectedScheme.department_name}</p>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Claim Amount (in INR)
                </label>
                <input
                  type="number"
                  value={claimAmount}
                  onChange={(e) => setClaimAmount(e.target.value)}
                  max={selectedScheme.max_subsidy_inr}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                />
                <span className="text-[11px] text-slate-400 mt-1 block">
                  Capped at maximum ceiling of ₹{selectedScheme.max_subsidy_inr.toLocaleString()}
                </span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Machinery / Plant & Expenditure Remarks
                </label>
                <textarea
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  placeholder="Specify eligible investment on CNC machinery, pollution control devices, or solar plant installation..."
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-800"
                  rows={3}
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowApplyModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 rounded-xl text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold"
                >
                  Submit Incentive Claim
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
