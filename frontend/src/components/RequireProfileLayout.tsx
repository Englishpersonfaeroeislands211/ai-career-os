import { createContext, useContext, useEffect } from "react";
import { Outlet } from "react-router-dom";
import { PageLoader } from "./AiLoadingState";
import { useActiveProfile } from "../hooks/useActiveProfile";
import type { Profile } from "../types";

interface ProfileRouteContextValue {
  profile: Profile;
  setProfile: (profile: Profile) => void;
}

const ProfileRouteContext = createContext<ProfileRouteContextValue | null>(null);

/** Redirects to welcome when no profile; provides profile to nested routes. */
export function RequireProfileLayout() {
  const { profile, setProfile, loading, requireProfile } = useActiveProfile();

  useEffect(() => {
    if (!loading && !profile) {
      requireProfile();
    }
  }, [loading, profile, requireProfile]);

  if (loading || !profile) {
    return <PageLoader variant="page" />;
  }

  return (
    <ProfileRouteContext.Provider value={{ profile, setProfile }}>
      <Outlet />
    </ProfileRouteContext.Provider>
  );
}

export function useProfileRoute(): ProfileRouteContextValue {
  const context = useContext(ProfileRouteContext);
  if (!context) {
    throw new Error("useProfileRoute must be used within RequireProfileLayout");
  }
  return context;
}
