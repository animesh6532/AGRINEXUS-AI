import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  location?: string;
  primaryCrop?: string;
  farmType?: string;
}

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password?: string) => Promise<void>;
  signup: (payload: { name: string; email: string; password?: string; location?: string; primaryCrop?: string }) => Promise<void>;
  logout: () => void;
  updateProfile: (profile: Partial<UserProfile>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_STORAGE_KEY = 'agrinexus_user_session';
const TOKEN_STORAGE_KEY = 'agrinexus_token';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(() => {
    try {
      const saved = localStorage.getItem(AUTH_STORAGE_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Hydrate user session from backend API if JWT token is present
  const hydrateSession = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const data = await api.getCurrentUser();
      if (data && data.user) {
        const profile: UserProfile = {
          id: data.user.id,
          name: data.farmer_profile?.full_name || data.user.full_name || data.user.email.split('@')[0],
          email: data.user.email,
          primaryCrop: 'Rice',
          farmType: 'Commercial Agronomy',
        };
        setUser(profile);
        localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(profile));
      }
    } catch (err) {
      console.warn('Backend auth hydration failed, clearing local token:', err);
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      localStorage.removeItem(AUTH_STORAGE_KEY);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    hydrateSession();
  }, [hydrateSession]);

  useEffect(() => {
    if (user) {
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(AUTH_STORAGE_KEY);
    }
  }, [user]);

  const login = async (email: string, password: string = 'password123') => {
    try {
      const res = await api.loginUser({ email, password });
      if (res && res.access_token) {
        localStorage.setItem(TOKEN_STORAGE_KEY, res.access_token);
        const newUser: UserProfile = {
          id: res.user.id,
          name: res.user.full_name || email.split('@')[0],
          email: res.user.email,
          primaryCrop: 'Rice',
          farmType: 'Commercial Agronomy',
        };
        setUser(newUser);
      }
    } catch (err: any) {
      // Fallback local auth for legacy dev if backend is offline
      const token = 'fallback_token_' + btoa(email);
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
      const newUser: UserProfile = {
        id: email,
        name: email.split('@')[0],
        email,
        primaryCrop: 'Rice',
        farmType: 'Commercial Agronomy',
      };
      setUser(newUser);
    }
  };

  const signup = async (payload: { name: string; email: string; password?: string; location?: string; primaryCrop?: string }) => {
    const pwd = payload.password || 'password123';
    try {
      const res = await api.registerUser({
        full_name: payload.name,
        email: payload.email,
        password: pwd,
      });
      if (res && res.access_token) {
        localStorage.setItem(TOKEN_STORAGE_KEY, res.access_token);
        const newUser: UserProfile = {
          id: res.user.id,
          name: res.user.full_name || payload.name,
          email: res.user.email,
          primaryCrop: payload.primaryCrop || 'Rice',
          farmType: 'Commercial Agronomy',
        };
        setUser(newUser);
      }
    } catch (err: any) {
      // Fallback
      await login(payload.email, pwd);
    }
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(AUTH_STORAGE_KEY);
    setUser(null);
  };

  const updateProfile = (updated: Partial<UserProfile>) => {
    if (user) {
      setUser({ ...user, ...updated });
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        signup,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
