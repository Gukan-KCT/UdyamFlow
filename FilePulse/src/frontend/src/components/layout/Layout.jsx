import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import AssistantPanel from "../AssistantPanel";

export function Layout({ children }) {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />
        <main className="flex-1 p-8 overflow-y-auto">
          <div className="mx-auto max-w-[1440px]">
            {children}
          </div>
        </main>
      </div>
      <AssistantPanel />
    </div>
  );
}


