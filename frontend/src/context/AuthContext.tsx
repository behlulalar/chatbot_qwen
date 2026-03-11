import React, { createContext, useContext, useState, useCallback } from 'react';

const AUTH_KEY = 'subu_admin_token';

interface AuthContextType {
  token: string | null;
  username: string | null;
  login: (token: string, username: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(AUTH_KEY));
  const [username, setUsername] = useState<string | null>(() => {
    try {
      const u = localStorage.getItem('subu_admin_username');
      return u;
    } catch {
      return null;
    }
  });

  const login = useCallback((t: string, u: string) => {
    setToken(t);
    setUsername(u);
    localStorage.setItem(AUTH_KEY, t);
    localStorage.setItem('subu_admin_username', u);
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUsername(null);
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem('subu_admin_username');
  }, []);

  return (
    <AuthContext.Provider
      value={{
        token,
        username,
        login,
        logout,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
