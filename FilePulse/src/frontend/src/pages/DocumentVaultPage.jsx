import { useState, useEffect } from "react";
import {
  FolderLock,
  FileCheck,
  AlertTriangle,
  UploadCloud,
  CheckCircle2,
  Clock,
  ShieldAlert,
  Sparkles,
  Database,
  ArrowRight,
  X,
  FileText,
} from "lucide-react";
import {
  fetchDocumentVault,
  uploadDocument,
  preValidateApplication,
  fetchVerifiedData,
  fetchApprovalCatalogue,
} from "../api/client";

export default function DocumentVaultPage() {
  const [vaultDocs, setVaultDocs] = useState([]);
  const [verifiedFields, setVerifiedFields] = useState([]);
  const [catalogue, setCatalogue] = useState([]);
  const [selectedApprovals, setSelectedApprovals] = useState(["APPR-CTE-PCB", "APPR-FIRE-NOC"]);
  const [preValidationResult, setPreValidationResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState(null);

  // Upload modal state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [docType, setDocType] = useState("PROJECT_REPORT");
  const [title, setTitle] = useState("");
  const [fileName, setFileName] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [docs, verData, cat] = await Promise.all([
        fetchDocumentVault(),
        fetchVerifiedData(),
        fetchApprovalCatalogue(),
      ]);
      setVaultDocs(docs);
      setVerifiedFields(verData);
      setCatalogue(cat);
      runPreValidation(["APPR-CTE-PCB", "APPR-FIRE-NOC"]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function runPreValidation(approvals = selectedApprovals) {
    setValidating(true);
    try {
      const res = await preValidateApplication({
        approval_ids: approvals,
        uploaded_doc_types: [],
      });
      setPreValidationResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setValidating(false);
    }
  }

  async function handleUpload(e) {
    e.preventDefault();
    if (!title || !fileName) return;
    try {
      await uploadDocument({
        doc_type: docType,
        title,
        file_name: fileName,
        file_size: 1024 * 350,
        mime_type: "application/pdf",
      });
      setShowUploadModal(false);
      setTitle("");
      setFileName("");
      const updatedDocs = await fetchDocumentVault();
      setVaultDocs(updatedDocs);
      runPreValidation();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-500/20 text-indigo-200 rounded-full text-xs font-semibold uppercase tracking-wider mb-4 border border-indigo-400/30">
            <FolderLock className="w-3.5 h-3.5" /> Zero-Redundancy Document Vault
          </div>
          <h1 className="text-3xl font-black tracking-tight text-white mb-2">
            Verified Document Vault & Pre-Validation
          </h1>
          <p className="text-slate-300 text-sm leading-relaxed">
            Store once, reuse everywhere. Pre-validate statutory documents prior to application submission to achieve 100% first-pass departmental approval without query loops.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700 font-bold">Dismiss</button>
        </div>
      )}

      {/* Verified Data Store Bar */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-sky-600" />
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
              Re-usable Verified Enterprise Data
            </h2>
          </div>
          <span className="text-xs text-emerald-600 font-bold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> API Verified Sources (NSDL / GSTN / MSME)
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {verifiedFields.map((field) => (
            <div key={field.field_key} className="bg-slate-50 p-4 rounded-xl border border-slate-200/80">
              <span className="text-[10px] uppercase font-bold text-slate-400">{field.field_key}</span>
              <p className="font-mono text-sm font-bold text-slate-800 truncate mt-0.5">{field.field_value}</p>
              <p className="text-[10px] text-slate-500 mt-1 truncate">Source: {field.verified_by_source}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Main Grid: Pre-Validation Engine + Vault Files */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interactive Pre-Validation */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-500" /> Pre-Validation Engine
              </h3>
              {preValidationResult && (
                <span
                  className={`px-3 py-1 rounded-full text-xs font-black ${
                    preValidationResult.is_valid
                      ? "bg-emerald-100 text-emerald-800"
                      : "bg-amber-100 text-amber-800"
                  }`}
                >
                  Score: {preValidationResult.score}%
                </span>
              )}
            </div>

            <p className="text-xs text-slate-500 leading-relaxed">
              Select planned clearances below to test your vault completeness against statutory requirements:
            </p>

            {/* Clearances Selection */}
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {catalogue.slice(0, 5).map((cat) => {
                const isChecked = selectedApprovals.includes(cat.approval_id);
                return (
                  <label
                    key={cat.approval_id}
                    className="flex items-center gap-2.5 p-2 bg-slate-50 hover:bg-slate-100 rounded-lg text-xs cursor-pointer border border-slate-200/60"
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => {
                        let next;
                        if (e.target.checked) next = [...selectedApprovals, cat.approval_id];
                        else next = selectedApprovals.filter((id) => id !== cat.approval_id);
                        setSelectedApprovals(next);
                        runPreValidation(next);
                      }}
                      className="rounded text-sky-600 focus:ring-sky-500"
                    />
                    <span className="font-medium text-slate-700 truncate">{cat.name}</span>
                  </label>
                );
              })}
            </div>

            {/* Validation Checklist Output */}
            {validating ? (
              <div className="p-6 text-center text-xs text-slate-400">Validating statutory compliance...</div>
            ) : preValidationResult ? (
              <div className="space-y-3 pt-3 border-t border-slate-100">
                <div className="p-3 bg-slate-50 rounded-xl text-xs text-slate-700 leading-relaxed border border-slate-200/80">
                  {preValidationResult.readiness_summary}
                </div>

                <div className="space-y-2">
                  {preValidationResult.validations.map((v) => (
                    <div
                      key={v.doc_type}
                      className={`p-3 rounded-xl border text-xs flex items-start gap-2.5 ${
                        v.status === "VALID"
                          ? "bg-emerald-50/50 border-emerald-200 text-emerald-900"
                          : v.status === "EXPIRED"
                          ? "bg-rose-50/50 border-rose-200 text-rose-900"
                          : "bg-amber-50/50 border-amber-200 text-amber-900"
                      }`}
                    >
                      {v.status === "VALID" ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      )}
                      <div>
                        <p className="font-bold">{v.name}</p>
                        <p className="text-[11px] opacity-80 mt-0.5">{v.message}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>

        {/* Right Column: Vault Documents List */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div>
                <h3 className="font-bold text-slate-800 text-base">Applicant Vault Documents</h3>
                <p className="text-xs text-slate-500">Stored centrally with SHA256 integrity signatures</p>
              </div>
              <button
                onClick={() => setShowUploadModal(true)}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
              >
                <UploadCloud className="w-4 h-4" />
                <span>Upload Document</span>
              </button>
            </div>

            <div className="divide-y divide-slate-100">
              {vaultDocs.map((doc) => (
                <div key={doc.document_id} className="p-5 hover:bg-slate-50/60 transition-colors flex items-center justify-between gap-4">
                  <div className="flex items-start gap-3.5">
                    <div className="p-2.5 bg-sky-50 text-sky-600 rounded-xl mt-0.5">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-mono text-[10px] font-bold px-2 py-0.5 bg-slate-100 text-slate-700 rounded">
                          {doc.doc_type}
                        </span>
                        <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" /> Verified
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-slate-900">{doc.title}</h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {doc.file_name} • {(doc.file_size / 1024).toFixed(0)} KB • SHA: {doc.hash_sha256.slice(0, 12)}...
                      </p>
                    </div>
                  </div>

                  <span className="text-xs font-medium text-slate-400 shrink-0">
                    Uploaded: {new Date(doc.created_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Upload Document Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-scaleIn">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-800 text-base">Add Document to Vault</h3>
              <button onClick={() => setShowUploadModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Document Category
                </label>
                <select
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
                >
                  <option value="PROJECT_REPORT">Detailed Project Report</option>
                  <option value="FACTORY_LAYOUT">Factory Layout Plan</option>
                  <option value="SITE_PLAN">Site Master Plan</option>
                  <option value="LAND_DEED">Land Ownership Deed</option>
                  <option value="CTE_PCB">Pollution Control Plan / ETP</option>
                  <option value="NOC_FIRE">Fire Safety Specification</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  Document Display Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Revised Factory Safety Blueprint 2026"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  File Name
                </label>
                <input
                  type="text"
                  value={fileName}
                  onChange={(e) => setFileName(e.target.value)}
                  placeholder="e.g. blueprint_rev4.pdf"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 rounded-xl text-xs font-bold hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold shadow-sm"
                >
                  Save to Vault
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
