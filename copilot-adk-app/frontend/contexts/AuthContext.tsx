"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import * as auth from "@/lib/auth";

type UserInfo = auth.UserInfo;

type AuthContextType = {
  user: UserInfo | null;
  token: string | null;
  loading: boolean;
  login: (token: string, user: UserInfo) => void;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedToken = auth.getToken();
    const savedUser = auth.getUser();
    setToken(savedToken);
    setUser(savedUser);
    
    // Restore user cookie on page load if user is logged in
    if (savedUser && typeof document !== "undefined") {
      document.cookie = `copilot_adk_user_id=${savedUser.user_id}; path=/; max-age=${60 * 60 * 24 * 7}; samesite=lax`;
      console.log(`🔄 RESTORE: Set user cookie from localStorage - copilot_adk_user_id=${savedUser.user_id}`);
    }
    
    setLoading(false);
  }, []);

  const login = (t: string, u: UserInfo) => {
    auth.setToken(t);
    auth.setUser(u);
    setToken(t);
    setUser(u);
    
    // Set user cookie IMMEDIATELY on login (critical for AG-UI)
    if (typeof document !== "undefined") {
      document.cookie = `copilot_adk_user_id=${u.user_id}; path=/; max-age=${60 * 60 * 24 * 7}; samesite=lax`;
      console.log(`🔐 LOGIN: Set user cookie - copilot_adk_user_id=${u.user_id}`);
    }
  };

  const logout = async () => {
    await auth.logout();
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
