"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import * as auth from "@/lib/auth";

type UserInfo = auth.UserInfo;

type AuthContextType = {
  user: UserInfo | null;
  token: string | null;
  loading: boolean;
  login: (token: string, user: UserInfo) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setToken(auth.getToken());
    setUser(auth.getUser());
    setLoading(false);
  }, []);

  const login = (t: string, u: UserInfo) => {
    auth.setToken(t);
    auth.setUser(u);
    setToken(t);
    setUser(u);
    if (typeof document !== "undefined") {
      document.cookie = `copilot_adk_user_id=${encodeURIComponent(u.user_id)}; path=/; max-age=${60 * 60 * 24 * 7}; samesite=lax`;
    }
  };

  const logout = () => {
    auth.logout();
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
