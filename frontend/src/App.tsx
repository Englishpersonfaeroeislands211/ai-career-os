import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AiProviderPage } from "./pages/AiProviderPage";
import { DashboardPage } from "./pages/DashboardPage";
import { OnboardingPage } from "./pages/OnboardingPage";
import { ReviewPage } from "./pages/ReviewPage";
import { SettingsPage } from "./pages/SettingsPage";
import { WelcomePage } from "./pages/WelcomePage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<WelcomePage />} />
        <Route path="/onboarding" element={<Navigate to="/onboarding/ai" replace />} />
        <Route path="/onboarding/ai" element={<AiProviderPage />} />
        <Route path="/onboarding/upload" element={<OnboardingPage />} />
        <Route path="/onboarding/review" element={<ReviewPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
