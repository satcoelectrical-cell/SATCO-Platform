import { Navigate, Route, Routes } from "react-router-dom";
import { RequireAuth } from "./auth/AuthProvider";
import { AppShell } from "./components/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { ProjectsPage, ProjectWorkspacePage } from "./pages/ProjectsPage";
import { JournalPage, MemoryPage } from "./pages/KnowledgePages";
import { ReportsPage } from "./pages/ReportPages";
import { AssistantPage } from "./pages/AssistantPage";
import { AccountPage, ActivatePage, BootstrapPage, ResetPage } from "./pages/OnboardingPages";
import { OrganizationAdminPage } from "./pages/OrganizationAdminPage";

export default function App() { return <Routes><Route path="/login" element={<LoginPage />} /><Route path="/bootstrap" element={<BootstrapPage />} /><Route path="/activate" element={<ActivatePage />} /><Route path="/reset" element={<ResetPage />} /><Route element={<RequireAuth><AppShell /></RequireAuth>}><Route index element={<DashboardPage />} /><Route path="projects" element={<ProjectsPage />} /><Route path="projects/:projectId" element={<ProjectWorkspacePage />} /><Route path="journal" element={<JournalPage />} /><Route path="reports" element={<ReportsPage />} /><Route path="reports/:reportId" element={<ReportsPage />} /><Route path="memory" element={<MemoryPage />} /><Route path="memory/:memoryId" element={<MemoryPage />} /><Route path="assistant" element={<AssistantPage />} /><Route path="account" element={<AccountPage />} /><Route path="organization-admin" element={<OrganizationAdminPage />} /></Route><Route path="*" element={<Navigate to="/" replace />} /></Routes>; }
