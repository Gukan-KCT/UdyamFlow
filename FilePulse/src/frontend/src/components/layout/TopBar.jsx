import { useState, useEffect } from "react";
import { User, ShieldCheck, RefreshCw, Check } from "lucide-react";
import { login, getActiveUser } from "../../api/client";

const DEMO_PERSONAS = [
  {
    role: "applicant",
    name: "Ramesh Sharma",
    org: "Apex Precision Auto Engineering",
    email: "applicant@udyamflow.gov.in",
    label: "Entrepreneur (Applicant)",
    badgeColor: "bg-sky-100 text-sky-800",
  },
  {
    role: "dept_officer_pcb",
    name: "Dr. Arvind Rao",
    org: "Pollution Control Board (PCB)",
    email: "officer.pcb@udyamflow.gov.in",
    label: "PCB Scrutiny Officer",
    badgeColor: "bg-emerald-100 text-emerald-800",
  },
  {
    role: "dept_officer_fire",
    name: "Vikram Rathore",
    org: "Fire & Emergency Services",
    email: "officer.fire@udyamflow.gov.in",
    label: "Divisional Fire Officer",
    badgeColor: "bg-orange-100 text-orange-800",
  },
  {
    role: "nodal_officer",
    name: "S. K. Verma, IAS",
    org: "Single Window Authority",
    email: "nodal@udyamflow.gov.in",
    label: "Nodal Authority / Collector",
    badgeColor: "bg-purple-100 text-purple-800",
  },
  {
    role: "admin",
    name: "Administrator",
    org: "System Governance",
    email: "admin@udyamflow.gov.in",
    label: "System Admin",
    badgeColor: "bg-slate-100 text-slate-800",
  },
];

export function TopBar() {
  const [currentUser, setCurrentUser] = useState(getActiveUser());
  const [switching, setSwitching] = useState(false);

  useEffect(() => {
    // If not logged in yet, default login as applicant
    if (!currentUser) {
      handleSwitchPersona(DEMO_PERSONAS[0]);
    }
  }, []);

  async function handleSwitchPersona(persona) {
    setSwitching(true);
    try {
      const data = await login(persona.email, "Demo@123");
      setCurrentUser(data.user);
      // Reload or refresh page context
      window.dispatchEvent(new Event("persona-changed"));
    } catch (err) {
      console.error("Persona switch error:", err);
    } finally {
      setSwitching(false);
    }
  }

  const activePersona =
    DEMO_PERSONAS.find((p) => p.email === currentUser?.email) || DEMO_PERSONAS[0];

  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200/80 px-8 py-3 flex flex-col sm:flex-row items-center justify-end gap-3 shadow-[0_2px_12px_rgba(0,0,0,0.03)]">
      {/* Role / Persona Switcher */}
      <div className="flex items-center gap-3">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          Active Persona:
        </span>

        <div className="relative">
          <select
            value={activePersona.email}
            disabled={switching}
            onChange={(e) => {
              const selected = DEMO_PERSONAS.find((p) => p.email === e.target.value);
              if (selected) handleSwitchPersona(selected);
            }}
            className="bg-slate-50 border border-slate-300 rounded-xl px-3 py-1.5 text-xs font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 cursor-pointer shadow-xs"
          >
            {DEMO_PERSONAS.map((p) => (
              <option key={p.email} value={p.email}>
                {p.label}: {p.name}
              </option>
            ))}
          </select>
        </div>

        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${activePersona.badgeColor}`}>
          {activePersona.org}
        </span>
      </div>
    </header>
  );
}
