import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Compass,
  CheckCircle2,
  Clock,
  Layers,
  FileText,
  Building2,
  DollarSign,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
  FolderLock,
  X,
} from "lucide-react";
import {
  fetchChecklistSectors,
  fetchChecklistStages,
  generateChecklist,
} from "../api/client";

export default function ChecklistWizardPage() {
  const [sectors, setSectors] = useState([]);
  const [stages, setStages] = useState([]);
  const [sector, setSector] = useState("Manufacturing");
  const [stage, setStage] = useState("Pre-Establishment");
  const [projectSize, setProjectSize] = useState("Small");
  const [locationType, setLocationType] = useState("Industrial Area");
  const [investmentCr, setInvestmentCr] = useState(7.5);
  const [turnoverCr, setTurnoverCr] = useState(18.0);
  const [result, setResult] = useState(null);
  const [activeGuideAppr, setActiveGuideAppr] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadMeta() {
      try {
        const [secData, stageData] = await Promise.all([
          fetchChecklistSectors(),
          fetchChecklistStages(),
        ]);
        setSectors(secData);
        setStages(stageData);
        handleGenerate(secData[0]?.id || "Manufacturing", stageData[0]?.id || "Pre-Establishment");
      } catch (err) {
        setError(err.message);
      }
    }
    loadMeta();
  }, []);

  async function handleGenerate(
    targetSector = sector,
    targetStage = stage,
    targetSize = projectSize,
    targetLoc = locationType
  ) {
    setLoading(true);
    setError(null);
    try {
      const data = await generateChecklist({
        sector: targetSector,
        stage: targetStage,
        project_size: targetSize,
        location_type: targetLoc,
        investment_cr: parseFloat(investmentCr),
        turnover_cr: parseFloat(turnoverCr),
      });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-sky-900 via-indigo-900 to-slate-900 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-80 h-80 rounded-full bg-sky-500/10 blur-3xl" />
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-sky-500/20 text-sky-200 rounded-full text-xs font-semibold uppercase tracking-wider mb-4 border border-sky-400/30">
            <Compass className="w-3.5 h-3.5" /> Regulatory Knowledge Engine
          </div>
          <h1 className="text-3xl font-black tracking-tight text-white mb-2">
            Intelligent Approval Checklist Wizard
          </h1>
          <p className="text-sky-100/90 text-sm leading-relaxed">
            Generate a customized, statutory approval checklist tailored to your enterprise sector, project scale, location, and operating stage. Parallel departmental workflows ensure approval timelines run concurrently.
          </p>
          <div className="mt-4 flex items-center gap-3 text-xs bg-amber-500/10 border border-amber-400/30 text-amber-200 px-3.5 py-2 rounded-lg">
            <AlertCircle className="w-4 h-4 text-amber-300 shrink-0" />
            <span>SAMPLE / ILLUSTRATIVE ENGINE — All rules and statutory SLAs for demonstration & SIH 2026 evaluation.</span>
          </div>
        </div>
      </div>

      {/* Configuration Card */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200/80">
        <h2 className="text-base font-bold text-slate-800 mb-4 flex items-center gap-2">
          <Building2 className="w-4 h-4 text-sky-600" /> Enter Enterprise Project Parameters
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* Sector */}
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
              Industrial Sector
            </label>
            <select
              value={sector}
              onChange={(e) => {
                setSector(e.target.value);
                handleGenerate(e.target.value, stage, projectSize, locationType);
              }}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              {sectors.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          {/* Stage */}
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
              Project Stage
            </label>
            <select
              value={stage}
              onChange={(e) => {
                setStage(e.target.value);
                handleGenerate(sector, e.target.value, projectSize, locationType);
              }}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              {stages.map((st) => (
                <option key={st.id} value={st.id}>
                  {st.name}
                </option>
              ))}
            </select>
          </div>

          {/* Project Size */}
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
              Enterprise Scale
            </label>
            <select
              value={projectSize}
              onChange={(e) => {
                setProjectSize(e.target.value);
                handleGenerate(sector, stage, e.target.value, locationType);
              }}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="Micro">Micro (&lt; ₹1 Cr Inv, &lt; ₹5 Cr Turn)</option>
              <option value="Small">Small (&lt; ₹10 Cr Inv, &lt; ₹50 Cr Turn)</option>
              <option value="Medium">Medium (&lt; ₹50 Cr Inv, &lt; ₹250 Cr Turn)</option>
              <option value="Large">Large / Mega Project</option>
            </select>
          </div>

          {/* Location */}
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
              Location / Land Type
            </label>
            <select
              value={locationType}
              onChange={(e) => {
                setLocationType(e.target.value);
                handleGenerate(sector, stage, projectSize, e.target.value);
              }}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="Industrial Area">Designated Industrial Park / MIDC</option>
              <option value="Rural / Panchayat">Rural Land / Gram Panchayat</option>
              <option value="Municipal / Urban">Municipal Corporation Area</option>
              <option value="Eco-sensitive Zone">Eco-Sensitive Buffer Zone</option>
            </select>
          </div>
        </div>
      </div>

      {/* Summary KPI Badges */}
      {result && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-sky-50 text-sky-600 rounded-xl">
              <Layers className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-slate-400">Total Approvals</p>
              <p className="text-2xl font-black text-slate-800">{result.total_approvals}</p>
              <p className="text-[11px] text-slate-500">Across {new Set(result.matched_approvals.map(a => a.department_id)).size} Departments</p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-slate-400">Critical Path SLA</p>
              <p className="text-2xl font-black text-emerald-600">{result.critical_path_sla_days} Days</p>
              <p className="text-[11px] text-slate-500">Parallel Composite Processing</p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl">
              <DollarSign className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-slate-400">Estimated Total Fees</p>
              <p className="text-2xl font-black text-slate-800">₹{result.estimated_total_fee.toLocaleString()}</p>
              <p className="text-[11px] text-slate-500">Unified Payment Gateway</p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-purple-50 text-purple-600 rounded-xl">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-slate-400">Statutory Safeguards</p>
              <p className="text-lg font-bold text-purple-700">Deemed Clearance</p>
              <p className="text-[11px] text-slate-500">Escalates automatically on SLA expiry</p>
            </div>
          </div>
        </div>
      )}

      {/* Matched Approvals List */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div>
            <h3 className="font-bold text-slate-800 text-base">Customised Required Clearances</h3>
            <p className="text-xs text-slate-500">Select any approval to inspect prerequisite documents and governing act</p>
          </div>
          <Link
            to="/applications"
            className="inline-flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
          >
            <span>Proceed to 1-Click Application</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 text-sm">Evaluating regulatory rule catalogue...</div>
        ) : result && result.matched_approvals.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {result.matched_approvals.map((appr, idx) => (
              <div key={appr.approval_id} className="p-6 hover:bg-slate-50/60 transition-colors">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[11px] font-mono font-bold">
                        {appr.approval_id}
                      </span>
                      <span className="px-2.5 py-0.5 bg-sky-50 text-sky-700 border border-sky-200 rounded-full text-xs font-bold">
                        {appr.department_name}
                      </span>
                      <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded text-xs font-semibold">
                        SLA: {appr.max_sla_days} Days
                      </span>
                    </div>
                    <h4 className="text-base font-bold text-slate-900">{appr.name}</h4>
                    <p className="text-xs text-slate-500 mt-1">
                      Statutory Authority: <span className="font-medium text-slate-700">{appr.statutory_act}</span> • Validity: <span className="font-medium text-slate-700">{appr.validity_years} Year(s)</span>
                    </p>

                    {/* Prerequisites and Required Documents */}
                    <div className="mt-3 flex flex-wrap gap-2">
                      {appr.documents_required.map((doc) => (
                        <span key={doc} className="inline-flex items-center gap-1 text-[11px] bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md">
                          <FileText className="w-3 h-3 text-slate-400" />
                          <span>Req: {doc}</span>
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-4 shrink-0">
                    <div className="text-right">
                      <p className="text-xs text-slate-400 uppercase font-bold">Statutory Fee</p>
                      <p className="text-lg font-black text-slate-800">₹{appr.fee_inr.toLocaleString()}</p>
                    </div>
                    <button
                      onClick={() => setActiveGuideAppr(appr)}
                      className="inline-flex items-center gap-1.5 px-3 py-2 bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200 rounded-xl text-xs font-bold transition-all"
                    >
                      <HelpCircle className="w-3.5 h-3.5" />
                      <span>Guidance</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center text-slate-500 text-sm">
            No mandatory clearances found matching the selected parameters.
          </div>
        )}
      </div>

      {/* Detailed Documentation Guidance Modal */}
      {activeGuideAppr && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-scaleIn">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 bg-sky-100 text-sky-800 rounded font-mono text-xs font-bold">
                  {activeGuideAppr.approval_id}
                </span>
                <h3 className="font-bold text-slate-800 text-base">Documentation & Compliance Guide</h3>
              </div>
              <button onClick={() => setActiveGuideAppr(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-700">
              <div>
                <p className="font-bold text-slate-900 text-sm">{activeGuideAppr.name}</p>
                <p className="text-slate-500 mt-0.5">Issuing Agency: <span className="font-bold text-sky-700">{activeGuideAppr.department_name}</span></p>
                <p className="text-slate-500">Statutory Framework: <span className="font-mono text-slate-700">{activeGuideAppr.statutory_act}</span></p>
              </div>

              <div className="p-3 bg-sky-50 rounded-xl border border-sky-200/60 space-y-1.5">
                <p className="font-bold text-sky-900 uppercase text-[10px] tracking-wider">Mandatory Prerequisites Checklist:</p>
                <ul className="list-disc list-inside space-y-1 text-slate-700">
                  {activeGuideAppr.prerequisites.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </div>

              <div className="p-3 bg-amber-50 rounded-xl border border-amber-200/60 space-y-1.5">
                <p className="font-bold text-amber-900 uppercase text-[10px] tracking-wider flex items-center gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                  Common Delay Pitfalls & Rejection Reasons:
                </p>
                <ul className="list-disc list-inside space-y-1 text-slate-700">
                  <li>Incomplete cadastral boundary coordinates or unregistered plot lease deeds.</li>
                  <li>Discrepancy between Machinery Layout blueprint and environmental effluent capacity.</li>
                  <li>Outdated NOCs or expired authorized signatory authorizations.</li>
                </ul>
              </div>

              <div className="flex justify-between items-center pt-2 border-t border-slate-100">
                <span className="text-[11px] text-slate-400">Statutory SLA: {activeGuideAppr.max_sla_days} Days</span>
                <Link
                  to="/vault"
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs"
                >
                  <FolderLock className="w-3.5 h-3.5" />
                  <span>Attach Documents from Vault</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
