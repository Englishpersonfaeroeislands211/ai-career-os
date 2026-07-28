import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Profile } from "../types";
import { getActiveProfileId, setActiveProfileId } from "../lib/profile";

export function useActiveProfile() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const profiles = await api.profiles.list();
        if (profiles.length === 0) {
          setProfile(null);
          return;
        }
        const activeId = getActiveProfileId();
        const active = profiles.find((p) => p.id === activeId) ?? profiles[0];
        setActiveProfileId(active.id);
        setProfile(active);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  function requireProfile() {
    if (!loading && !profile) {
      navigate("/welcome", { replace: true });
      return false;
    }
    return true;
  }

  return { profile, setProfile, loading, requireProfile };
}
