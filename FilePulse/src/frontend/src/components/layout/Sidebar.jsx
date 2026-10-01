import { Link, useLocation } from "react-router-dom";
import {
  Compass,
  FileText,
  FolderLock,
  Calendar,
  ShieldCheck,
  Sparkles,
  Scale,
  Activity,
  Layers,
  Network,
  ChevronRight,
  Building2,
  AlertTriangle,
  LayoutDashboard,
} from "lucide-react";
import { cn } from "../../utils/classNames";

export function Sidebar() {
  const location = useLocation();

  const entrepreneurLinks = [
    { path: "/", label: "Executive Dashboard", icon: LayoutDashboard },
    { path: "/checklist", label: "Checklist Wizard", icon: Compass },
    { path: "/applications", label: "Single-Window Apps", icon: Layers },
    { path: "/vault", label: "Document Vault", icon: FolderLock },
    { path: "/inspections", label: "Common Inspections", icon: Calendar },
    { path: "/compliance", label: "Compliance & Renewals", icon: ShieldCheck },
    { path: "/schemes", label: "Schemes & Subsidies", icon: Sparkles },
    { path: "/grievances", label: "Grievance Redressal", icon: Scale },
  ];

  const analyticsLinks = [
    { path: "/delay-analytics", label: "Delay Radar & Bottlenecks", icon: Activity },
    { path: "/legacy-radar", label: "e-Office Radar (Legacy)", icon: FileText },
    { path: "/org", label: "Department Hierarchy", icon: Network },
  ];

  return (
    <aside className="w-72 bg-white/90 backdrop-blur-xl border-r border-slate-200/80 h-screen sticky top-0 flex flex-col shadow-[4px_0_24px_rgba(0,0,0,0.02)] z-40 select-none">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-gradient-to-b from-slate-50 to-transparent">
        <Link to="/applications" className="flex items-center gap-3">
          <div className="bg-sky-600 p-2.5 rounded-xl shadow-md border border-sky-500 text-white">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-black text-slate-800 tracking-tight flex items-center gap-1.5">
              <span>UdyamFlow</span>
            </h1>
            <p className="text-[10px] text-sky-600 font-bold uppercase tracking-widest mt-0.5">
              Single-Window Approval Portal
            </p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-6 overflow-y-auto">
        {/* Entrepreneur Portal Links */}
        <div>
          <div className="px-3 mb-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            Single-Window Clearances
          </div>
          <div className="space-y-1">
            {entrepreneurLinks.map((link) => {
              const active = location.pathname === link.path;
              const Icon = link.icon;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={cn(
                    "group flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all relative overflow-hidden",
                    active
                      ? "text-sky-800 bg-sky-50 shadow-xs border border-sky-100 font-bold"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900 border border-transparent"
                  )}
                >
                  {active && (
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-sky-500 rounded-r-full shadow-sm" />
                  )}
                  <div className="flex items-center gap-2.5">
                    <Icon
                      className={cn(
                        "w-4 h-4 transition-transform",
                        active ? "text-sky-600 scale-105" : "text-slate-400 group-hover:text-slate-600"
                      )}
                    />
                    <span>{link.label}</span>
                  </div>
                  {active && <ChevronRight className="w-3.5 h-3.5 text-sky-400" />}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Diagnostics & Authority */}
        <div>
          <div className="px-3 mb-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            Delay Analytics & Radar
          </div>
          <div className="space-y-1">
            {analyticsLinks.map((link) => {
              const active = location.pathname === link.path;
              const Icon = link.icon;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={cn(
                    "group flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all relative overflow-hidden",
                    active
                      ? "text-sky-800 bg-sky-50 shadow-xs border border-sky-100 font-bold"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900 border border-transparent"
                  )}
                >
                  {active && (
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-sky-500 rounded-r-full shadow-sm" />
                  )}
                  <div className="flex items-center gap-2.5">
                    <Icon
                      className={cn(
                        "w-4 h-4 transition-transform",
                        active ? "text-sky-600 scale-105" : "text-slate-400 group-hover:text-slate-600"
                      )}
                    />
                    <span>{link.label}</span>
                  </div>
                  {active && <ChevronRight className="w-3.5 h-3.5 text-sky-400" />}
                </Link>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Footer Pill */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50">
        <div className="p-3 bg-white rounded-xl shadow-xs border border-slate-200">
          <p className="text-[11px] font-bold text-slate-800">Apex Precision Auto Engineering</p>
          <p className="text-[10px] text-slate-400 truncate">UDYAM-MH-26-0012345 • Pune</p>
        </div>
      </div>
    </aside>
  );
}
