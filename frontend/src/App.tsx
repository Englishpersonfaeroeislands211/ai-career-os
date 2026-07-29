import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AiProviderPage } from "./pages/AiProviderPage";
import { HomePage } from "./pages/HomePage";
import { JobDetailPage } from "./pages/JobDetailPage";
import { JobNewPage } from "./pages/JobNewPage";
import { JobReviewPage } from "./pages/JobReviewPage";
import { OnboardingPage } from "./pages/OnboardingPage";
import { ProfilePage } from "./pages/ProfilePage";
import { ReviewPage } from "./pages/ReviewPage";
import { SettingsPage } from "./pages/SettingsPage";
import { WelcomePage } from "./pages/WelcomePage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/welcome" element={<WelcomePage />} />
        <Route path="/onboarding" element={<Navigate to="/onboarding/ai" replace />} />
        <Route path="/onboarding/ai" element={<AiProviderPage />} />
        <Route path="/onboarding/upload" element={<OnboardingPage />} />
        <Route path="/onboarding/review" element={<ReviewPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/jobs/new" element={<JobNewPage />} />
        <Route path="/jobs/new/review" element={<JobReviewPage />} />
        <Route path="/jobs/:id" element={<JobDetailPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/dashboard" element={<Navigate to="/" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
