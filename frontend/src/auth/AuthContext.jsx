import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import { api, setOnAuthFailure } from "../api/client";
import { clearTokens, getAccess, getRefresh, setTokens } from "./tokenStore";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    try {
      const { data } = await api.get("/auth/me/");
      setUser(data);
      return data;
    } catch {
      setUser(null);
      return null;
    }
  }, []);

  const login = useCallback(
    async (tokens) => {
      setTokens(tokens);
      return loadUser();
    },
    [loadUser]
  );

  const logout = useCallback(async () => {
    const refresh = getRefresh();
    if (refresh) {
      try {
        await api.post("/auth/logout/", { refresh });
      } catch {
        // token may already be expired or blacklisted; clear locally anyway
      }
    }
    clearTokens();
    setUser(null);
  }, []);

  useEffect(() => {
    setOnAuthFailure(() => setUser(null));

    async function bootstrap() {
      if (getAccess()) {
        await loadUser();
      }
      setLoading(false);
    }

    bootstrap();
  }, [loadUser]);

  const value = {
    user,
    loading,
    login,
    logout,
    refreshUser: loadUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider.");
  }
  return context;
}
