import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./components/layout/Layout";
import SingleWindowDashboardPage from "./pages/SingleWindowDashboardPage";
import ChecklistWizardPage from "./pages/ChecklistWizardPage";
import SingleWindowApplicationsPage from "./pages/SingleWindowApplicationsPage";
import DocumentVaultPage from "./pages/DocumentVaultPage";
import InspectionsPage from "./pages/InspectionsPage";
import ComplianceRenewalsPage from "./pages/ComplianceRenewalsPage";
import SchemesPage from "./pages/SchemesPage";
import GrievancesPage from "./pages/GrievancesPage";
import DelayAnalyticsPage from "./pages/DelayAnalyticsPage";
import DashboardPage from "./pages/DashboardPage";
import OrgTreePage from "./pages/OrgTreePage";
import FileDetailPage from "./pages/FileDetailPage";
import FileJourneyPage from "./pages/FileJourneyPage";
import EmployeeDetailPage from "./pages/EmployeeDetailPage";

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<SingleWindowDashboardPage />} />
          <Route path="/dashboard" element={<SingleWindowDashboardPage />} />
          <Route path="/checklist" element={<ChecklistWizardPage />} />
          <Route path="/applications" element={<SingleWindowApplicationsPage />} />
          <Route path="/vault" element={<DocumentVaultPage />} />
          <Route path="/inspections" element={<InspectionsPage />} />
          <Route path="/compliance" element={<ComplianceRenewalsPage />} />
          <Route path="/schemes" element={<SchemesPage />} />
          <Route path="/grievances" element={<GrievancesPage />} />
          <Route path="/delay-analytics" element={<DelayAnalyticsPage />} />
          
          {/* Legacy e-Office Radar Routes */}
          <Route path="/legacy-radar" element={<DashboardPage />} />
          <Route path="/org" element={<OrgTreePage />} />
          <Route path="/employees/:id" element={<EmployeeDetailPage />} />
          <Route path="/files/:id" element={<FileDetailPage />} />
          <Route path="/files/:id/journey" element={<FileJourneyPage />} />
          
          <Route path="*" element={<Navigate to="/applications" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
